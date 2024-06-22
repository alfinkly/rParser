from sqlalchemy import select, insert, update
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
            db_product: Product | None = result.scalar()
            if db_product is None:
                session.add(product)
            elif product != db_product:
                query = (
                    update(Product)
                    .values(name=product.name,
                            link=product.link,
                            price=product.price,
                            image_url=product.image_url)
                    .filter_by(link=db_product.link)
                )
                await session.execute(query)
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

    async def search_by_id(self, id: int):
        async with self.sessionmaker() as session:
            query = (
                select(Product)
                .filter(Product.id == id)
                .options(selectinload(Product.category).selectinload(Category.site))
            )
            result = await session.execute(query)
            products = result.unique().scalars().one()
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
                    query = (
                        insert(ProductMatch)
                        .values(first_product_id=id_x, second_product_id=id_y)
                    )
                    await session.execute(query)
            await session.commit()

    async def select_all(self):
        async with self.sessionmaker() as session:
            query = select(ProductMatch)
            result = await session.execute(query)
            products_match = result.scalars().all()
            return products_match

    async def select_by_id(self, id: int):
        async with self.sessionmaker() as session:
            query = (
                select(ProductMatch)
                .filter_by(id=id)
            )
            result = await session.execute(query)
            product_match = result.scalars().one()
            return product_match