from sqlalchemy import select

from database.models import GeneralProduct
from database.repo.repo import Repo


class MatchClickCounterRepo(Repo):
    async def select_all(self):
        with self.sessionmaker() as session:
            query = (
                select(GeneralProduct)
            )
            result = await session.execute(query)
            general_products = result.scalars().all()
            return general_products