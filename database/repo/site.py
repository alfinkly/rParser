from typing import Any, Sequence

from sqlalchemy import update, select, insert, Row, RowMapping
from database.repo.repo import Repo
from database.models import Site


class SiteRepo(Repo):
    async def start_fill(self):
        async with self.sessionmaker() as session:
            session.add_all([
                Site(id=1, name='clever'),
                Site(id=2, name='arbuz'),
                Site(id=3, name='kaspi')
            ])
            await session.commit()

    async def select_sites(self) -> Sequence | list[Site]:
        async with self.sessionmaker() as session:
            query = (
                select(Site)
            )
            result = await session.execute(query)
            urls = result.scalars().all()
            return urls