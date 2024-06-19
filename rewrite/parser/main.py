from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from database.database import ORM


class Parser:
    def __init__(self, orm: ORM):
        self.orm = orm
        self.driver = self.initialize_driver()
        self.wait = WebDriverWait(self.driver, 2000)

    @staticmethod
    def initialize_driver():
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.headless = True
        return webdriver.Firefox(options=options)

    def parse(self):
        pass