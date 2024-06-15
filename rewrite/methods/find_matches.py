import nltk as nltk
import numpy as np
import pandas as pd
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.database import ORM

# Ensure you have the necessary NLTK data files
nltk.download('stopwords')
nltk.download('wordnet')


async def find_matches(orm: ORM):
    site1_products = await orm.product_repo.select_site_products(1)
    site2_products = await orm.product_repo.select_site_products(2)
    site3_products = await orm.product_repo.select_site_products(3)

    def products_to_df(products, site_name):
        return pd.DataFrame([(p.id, p.name, site_name) for p in products], columns=['id', 'product', 'site_id'])

    df_site1 = products_to_df(site1_products, 'site1')
    df_site2 = products_to_df(site2_products, 'site2')
    df_site3 = products_to_df(site3_products, 'site3')

    # Объединение всех данных в один DataFrame
    merged_data = pd.concat([df_site1, df_site2, df_site3])

    # Пример функции нормализации строк
    # Пример функции нормализации строк
    def normalize_string(s):
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('russian'))  # Assuming product names are in Russian
        words = ''.join(e for e in s if e.isalnum() or e.isspace()).lower().split()
        return ' '.join(lemmatizer.lemmatize(word) for word in words if word not in stop_words)

    # Нормализуем названия продуктов
    merged_data['product_norm'] = merged_data['product'].apply(normalize_string)

    # Используем TF-IDF Vectorizer для сравнения строк
    vectorizer = TfidfVectorizer().fit_transform(merged_data['product_norm'])
    cosine_similarities = cosine_similarity(vectorizer)

    # Устанавливаем порог схожести для определения совпадений
    threshold = 0.8

    # Находим все совпадения по порогу схожести
    matches = np.argwhere(cosine_similarities > threshold)

    # Создаем DataFrame с результатами
    result = pd.DataFrame(matches, columns=['id_x', 'id_y'])

    # Удаляем самосовпадения и дубликаты
    result = result[result['id_x'] != result['id_y']]
    result = result.drop_duplicates()

    # Преобразуем индексы обратно в идентификаторы продуктов
    result['id_x'] = merged_data.iloc[result['id_x']]['id'].values
    result['id_y'] = merged_data.iloc[result['id_y']]['id'].values

    with open('matched_products.txt', 'w', encoding='utf-8') as f:
        for index, row in result.iterrows():
            id_x, id_y = row['id_x'], row['id_y']
            product_x = merged_data.loc[merged_data['id'] == id_x, 'product'].values[0]
            product_y = merged_data.loc[merged_data['id'] == id_y, 'product'].values[0]
            f.write(f"Product 1: {product_x} (ID: {id_x}) - Product 2: {product_y} (ID: {id_y})\n")

    # Сохраняем результат в CSV
    result.to_csv('matched_products.csv', index=False)

    print(result)