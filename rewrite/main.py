import asyncio
import logging
import argparse
from sqlalchemy.ext.asyncio import async_sessionmaker

from arbuz.main import parse_arbuz
from clever.main import parse_clever
from database.database import ORM
from database.site import UrlRepo
from methods.find_matches import find_matches
from tgbot.bot import run_tgbot


orm = ORM()
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tgbot', action="store_true")
parser.add_argument('-p', '--parsers', action="store_true")
parser.add_argument('-r', '--recreate_db', action="store_true")
parser.add_argument('-f', '--find_matches', action="store_true")
args = parser.parse_args()


async def start():
    await orm.create_repos()
    if args.find_matches:
        return await find_matches(orm)
    if args.recreate_db:
        return orm.recreate_tables()

    tasks = []
    if args.tgbot:
        tasks.append(asyncio.create_task(run_tgbot(orm)))
    if args.parsers:
        tasks.append(asyncio.create_task(parse_clever(orm)))
        tasks.append(asyncio.create_task(parse_arbuz(orm)))
    await asyncio.gather(*tasks)

asyncio.run(start())