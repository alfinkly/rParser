import asyncio
import logging
import argparse

import coloredlogs as coloredlogs
from pyfiglet import figlet_format
from termcolor import colored
from parser.arbuz import ArbuzParser
from parser.clever import CleverParser
from database.database import ORM
from parser.kaspi import KaspiParser
from methods.find_matches import ProductMatcher
from tgbot.bot import run_tgbot

print("\n"*2 + colored(figlet_format('by alfinkly', font='thin', width=200), 'magenta') + "\n"*4)

orm = ORM()
logging.basicConfig(level=orm.settings.logging_level)
coloredlogs.install()
parser = argparse.ArgumentParser(description='shoparser by alfinkly')
parser.add_argument('-t', '--tgbot', action="store_true", help='Запуск телеграм-бота')
parser.add_argument('-p', '--parsers', nargs='+', type=str, help='Список парсеров (например, kaspi clever arbuz)')
parser.add_argument('-r', '--recreate_db', action="store_true", help='Пересоздание базы данных')
parser.add_argument('-f', '--find_matches', action="store_true", help='Поиск совпадений продуктов')
args = parser.parse_args()


async def start():
    await orm.create_repos()
    tasks = []

    if args.recreate_db:
        orm.recreate_tables()
    if args.tgbot:
        tasks.append(asyncio.create_task(run_tgbot(orm)))
    if args.parsers:
        if 'kaspi' in args.parsers:
            kaspi_parser = KaspiParser(orm)
            tasks.append(asyncio.create_task(kaspi_parser.parse()))
        if 'clever' in args.parsers:
            clever_parser = CleverParser(orm)
            tasks.append(asyncio.create_task(clever_parser.parse()))
        if 'arbuz' in args.parsers:
            arbuz_parser = ArbuzParser(orm)
            tasks.append(asyncio.create_task(arbuz_parser.parse()))
    if args.find_matches:
        general_producter = ProductMatcher(orm)
        tasks.append(asyncio.create_task(general_producter.find_matches_products()))
        # tasks.append(asyncio.create_task(general_producter.loop_general_product()))

    logging.info(f"{tasks=}")
    await asyncio.gather(*tasks)


asyncio.run(start())
