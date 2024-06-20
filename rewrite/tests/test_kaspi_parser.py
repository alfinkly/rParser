from database.database import ORM
from parser.kaspi import KaspiParser


class TestKaspi:
    def __init__(self):
        self.orm = ORM()
        self.orm.create_repos()

    def kaspi_parse(self):
        parser = KaspiParser(orm=self.orm)
        parser.parse()
