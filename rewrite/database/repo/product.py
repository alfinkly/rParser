from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.repo.repo import Repo
from database.models import Product, Category, Site, ProductMatch


class ProductRepo(Repo):
    async def insert_or_update_product(self, product: Product):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter_by(link=product.link)
            )
            result = await session.execute(query)
            if result.one_or_none() is None:
                session.add(product)
                await session.commit()

    async def select_all(self):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .options(selectinload(Product.category))
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def select_site_products(self, site_id: int):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .join(Category)
                .join(Site)
                .where(Site.id == site_id)
            )
            result = await session.execute(query)
            products = result.scalars().all()
            return products

    async def search_by_name(self, name: str):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter(Product.name.ilike(f'%{name}%'))
            )
            result = await session.execute(query)
            products = result.unique().scalars().all()
            await session.close()
            return products

    async def search_by_category(self, id: int):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter_by(category_id=id)
            )
            result = await session.execute(query)
            products = result.scalars().all()
            await session.close()
            return products


class ProductMatchRepo(Repo):
    async def insert_or_update_products_match(self, products):
        async with self.sessionmaker() as session:
            unique_pairs = set()
            for index, row in products.iterrows():
                id_x, id_y = row['id_x'], row['id_y']
                unique_pairs.add((id_x, id_y))

            stmt = select(ProductMatch)
            result = await session.execute(stmt)
            products_match = result.scalars().all()
            products_match = [(pm.first_product_id, pm.second_product_id) for pm in products_match]
            for id_x, id_y in unique_pairs:
                if (id_x, id_y) not in products_match:
                    product_match = ProductMatch(first_product_id=id_x, second_product_id=id_y)
                    session.add(product_match)

            await session.commit()

    async def select_all(self):
        async with self.sessionmaker() as session:
            query = select(ProductMatch)
            result = await session.execute(query)
            products_match = result.scalars().all()
            return products_match