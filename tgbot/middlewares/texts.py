import json

from database.models import Product


class Text:
    def __init__(self):
        with open("texts.json") as text:
            self.json = json.load(text)

    def get(self, tag: str):
        tags = tag.split(".")
        tag_value = self.json
        for t in tags:
            tag_value = tag_value[t]
        tag_value = tag_value.encode("windows-1251").decode("utf8")
        return tag_value

    @staticmethod
    def build_general_product_text(products: list[Product]):
        text = ""
        for num, p in enumerate(products):
            text += f"\n<b>{p.name}</b>\nЦена: {p.price}\n" \
                    f"<a href='{p.link}'>Ссылка на товар в {p.category.site.name}</a>\n"
            if num < len(products) - 1:
                text += f"↕️"
        return text