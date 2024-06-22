from database.models import ProductMatch, Product


class TextBuilder:
    @staticmethod
    def build_product_match_text(products: list[Product]):
        text = ""
        for num, p in enumerate(products):
            text += f"\n<b>{p.name}</b>\nЦена: {p.price}\n" \
                    f"<a href='{p.link}'>Ссылка на товар в {p.category.site.name}</a>\n"
            if num < len(products)-1:
                text += f"↕️"
        return text