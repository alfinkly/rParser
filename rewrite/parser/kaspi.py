import datetime
import hashlib
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup

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

    def _click_next_button(self):
        next_button = self.wait.until(expected_conditions.element_to_be_clickable(
            (By.XPATH, "//li[contains(@class, 'pagination__el') and contains(., 'Следующая')]")
        ))
        next_button.click()

    async def parse(self):
        urls = await self.orm.url_repo.select_urls(3)
        for url in urls:
            self.driver.get(url.url)
            last_successful_parse_time = datetime.datetime.now()
            last_page_hash = self._get_html_hash()

            while True:
                self.wait.until(expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'item-card')))
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all('div', class_="item-card")
                category_name = soup.find('h1', class_="breadcrumbs__item").text.removesuffix("в Астане")
                if not cards and (datetime.datetime.now() - last_successful_parse_time).seconds > 20:
                    break

                await self._parse_cards(cards, category_name)
                self._click_next_button()
                time.sleep(5)
                new_page_hash = self._get_html_hash()
                if self._get_html_hash() == last_page_hash:
                    break
                last_page_hash = new_page_hash

        time.sleep(self.orm.settings.timer)
