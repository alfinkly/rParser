from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.repo.category import CategoryRepo, GeneralCategoryRepo
from database.config import EnvSettings
from database.models import Base
from database.repo.product import ProductRepo, GeneralProductRepo
from database.repo.url import UrlRepo
from database.repo.user import UserRepo
from database.repo.site import SiteRepo


class ORM:
    def __init__(self):
        self.settings = EnvSettings()
        self.url_repo: UrlRepo = None
        self.site_repo: SiteRepo = None
        self.category_repo: CategoryRepo = None
        self.product_repo: ProductRepo = None
        self.user_repo: UserRepo = None
        self.general_category_repo: GeneralCategoryRepo = None
        self.general_product_repo: GeneralProductRepo = None

    async def get_async_engine(self, echo=False):
        async_engine = create_async_engine(
            url=self.settings.asyncpg_url(),
            echo=echo
        )
        return async_engine

    def get_engine(self):
        async_engine = create_engine(
            url=self.settings.psycopg_url(),
            echo=True
        )
        return async_engine

    async def recreate_tables(self):
        engine = self.get_engine()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        await self.site_repo.start_fill()

        engine.echo = True

    async def get_async_sessionmaker(self) -> async_sessionmaker:
        return async_sessionmaker(await self.get_async_engine())

    async def create_repos(self):
        sessionmaker = await self.get_async_sessionmaker()
        self.url_repo = UrlRepo(sessionmaker)
        self.site_repo = SiteRepo(sessionmaker)
        self.category_repo = CategoryRepo(sessionmaker)
        self.product_repo = ProductRepo(sessionmaker)
        self.user_repo = UserRepo(sessionmaker)
        self.general_category_repo = GeneralCategoryRepo(sessionmaker)
        self.general_product_repo = GeneralProductRepo(sessionmaker)