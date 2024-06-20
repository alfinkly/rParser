import os

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from database.database import ORM


class Parser:
    def __init__(self, orm: ORM):
        self.orm = orm
        self.driver = self.initialize_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def initialize_driver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.headless = True
        service = webdriver.FirefoxService(executable_path=self.orm.settings.geckodriver_src)
        return webdriver.Firefox(options=options, service=service)

    def parse(self):
        pass