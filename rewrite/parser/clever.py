from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from database.models import Product, Category
from parser.main import Parser


class CleverParser(Parser):
    async def insert_product(self, card, category_name):
        product = Product()
        product.name = card.find_element(By.CLASS_NAME, "product-card-title").text.strip()
        product.price = card.find_element(By.CLASS_NAME, "text-sm").text.strip()
        product.image_url = card.find_element(By.TAG_NAME, "img").get_attribute("src")
        product.link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

        category = Category()
        category.name = category_name
        category.site_id = 1
        product.category_id = await self.orm.category_repo.get_category_id(category)
        await self.orm.product_repo.insert_or_update_product(product)

    async def parse(self):
        while True:
            category_urls = await self.orm.url_repo.select_urls(1)
            for category_url in category_urls:
                self.driver.get(category_url.url)
                time.sleep(self.orm.settings.small_sleep)

                category_name_element = self.driver.find_element(By.CLASS_NAME, 'description-sm')
                category_name = category_name_element.text.strip()

                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(self.orm.settings.small_sleep)

                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                product_cards = self.driver.find_elements(By.CLASS_NAME, 'product-card')
                for card in product_cards:
                    await self.insert_product(card, category_name)

            time.sleep(self.orm.settings.timer)