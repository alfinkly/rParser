import datetime
import hashlib
import logging
import time

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup
from termcolor import colored

from database.models import Url, Category, Product
from parser.main import Parser


class KaspiParser(Parser):
    def _get_html_hash(self):
        page_source = self.driver.page_source.encode('utf-8')
        return hashlib.sha256(page_source).hexdigest()

    async def _parse_cards(self, cards, category_title):
        for card in cards:
            name_link = card.find('a', class_='item-card__name-link')
            product_url = name_link['href'] if name_link and name_link.has_attr('href') else 'Нет ссылки'

            price_tag = card.find('span', class_='item-card__prices-price')
            image_tag = card.find('img', class_='item-card__image')

            product = Product()
            product.name = name_link.text.strip() if name_link else 'Нет названия'
            product.price = price_tag.text.strip() if price_tag else 'Нет цены'
            product.image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else 'Нет изображения'
            product.link = product_url

            category = Category()
            category.name = category_title
            category.site_id = 3
            product.category_id = await self.orm.category_repo.get_category_id(category)
            await self.orm.product_repo.insert_or_update_product(product)

    async def parse(self):
        logging.info(colored("kaspi parser started", "cyan"))
        while True:
            start = datetime.datetime.now()
            urls = await self.orm.url_repo.select_urls(3)
            for url in urls:
                counter = 1
                while True:
                    self.driver.get(url.url + f"?page={counter}")
                    try:
                        self.wait.until(
                            expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'item-card'))
                        )
                    except TimeoutException:
                        break
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, "html.parser")
                    cards = soup.find_all('div', class_="item-card")
                    category_name = soup.find('h1', class_="breadcrumbs__item").text.removesuffix("в Астане")
                    # if not cards and (datetime.datetime.now() - last_successful_parse_time).seconds > 20:
                    #     break

                    await self._parse_cards(cards, category_name)
                    counter += 1
            end = datetime.datetime.now()
            delta = end - start
            print("\n" * 20 + "kaspi delta --- " + str(delta))
            time.sleep(self.orm.settings.timer)