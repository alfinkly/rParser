from database.models import Category, GeneralCategory


def generate_categories_text(g_category: GeneralCategory):
    text = f"Продукты в категории <b>{g_category.name}</b>:"
    for c in g_category.categories:
        c: Category
        text += f"<b>\n\n{c.name}:\n</b>"
        text += "\n".join([c.products[i].name for i in range(len(c.products[0:10]))])
        if len(c.products) > 10:
            text += f"\nеще {len(c.products) - 10} продуктов..."
    return text