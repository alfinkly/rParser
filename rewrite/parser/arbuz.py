from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from database.models import Product, Category
from parser.main import Parser


class ArbuzParser(Parser):
    async def parse_page(self, category_url, category_name):
        self.driver.get(category_url)
        self.wait.until(
            expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.product-item.product-card'))
        )

        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        product_cards = soup.find_all('article', class_='product-item product-card')

        for card in product_cards:
            product = Product()
            product.name = card.find('a', class_='product-card__title').text.strip()
            product.price = card.find('span', class_='price--wrapper').text.strip()
            product.image_url = card.find('img', class_='product-card__img').get('data-src')
            product.link = 'https://arbuz.kz' + card.find('a', class_='product-card__link').get('href')

            category = Category()
            category.name = category_name
            category.site_id = 2
            product.category_id = (await self.orm.category_repo.get_category_id(category))
            await self.orm.product_repo.insert_or_update_product(product)

    async def parse(self):
        while True:
            category_urls = await self.orm.url_repo.select_urls(2)
            for url in category_urls:
                base_url_template = url.url + '#/?%5B%7B%22slug%22%3A%22page%22,' \
                                              '%22value%22%3A{}%2C%22component%22%3A%22pagination%22%7D%5D'
                page_url = base_url_template.format(1)
                self.driver.get(page_url)
                time.sleep(10)
                page_buttons = self.driver.\
                    find_elements(By.XPATH, '/html/body/div[1]/main/section/div/section/div[2]/div[6]/nav/ul/*')
                category_name = self.driver.\
                    find_element(By.XPATH, '/html/body/div[1]/main/section/div/div[1]/nav/div/div/a').text

                for page_number in range(1, int(page_buttons[-2].text) + 1):
                    page_url = base_url_template.format(page_number)
                    self.driver.get(page_url)
                    time.sleep(10)
                    self.driver.execute_script("window.location.reload();")
                    self.wait.until(
                        expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                                              'article.product-item.product-card'))
                    )
                    await self.parse_page(page_url, category_name)
            time.sleep(self.orm.settings.timer)