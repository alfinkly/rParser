import time
import nltk
import numpy as np
import pandas as pd
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.database import ORM
from database.models import Product


class ProductMatcher:
    def __init__(self, orm: ORM):
        nltk.download('stopwords')
        nltk.download('wordnet')
        self.orm = orm
        self.custom_stop_words = {}
        self.threshold = 0.5

    async def fetch_products(self, site_id):
        return await self.orm.product_repo.select_site_products(site_id)

    @staticmethod
    def products_to_df(products):
        return pd.DataFrame([(p.id, p.name, p.category.site_id) for p in products],
                            columns=['id', 'product', 'site_id'])

    def normalize_string(self, s):
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('russian'))
        stop_words.update(self.custom_stop_words)
        words = ''.join(e for e in s if e.isalnum() or e.isspace()).lower().split()
        return ' '.join(lemmatizer.lemmatize(word) for word in words if word not in stop_words)

    def preprocess_products(self, merged_data):
        merged_data['product_norm'] = merged_data['product'].apply(self.normalize_string)
        return merged_data

    @staticmethod
    def find_similarities(merged_data):
        vectorizer = TfidfVectorizer().fit_transform(merged_data['product_norm'])
        cosine_similarities = cosine_similarity(vectorizer)
        return cosine_similarities

    def create_result_df(self, merged_data, similarities):
        results = []
        for idx, row in merged_data.iterrows():
            site_ids_seen = set()
            similarities_for_idx = similarities[idx]
            similar_products = np.argsort(similarities_for_idx)[::-1]
            for similar_idx in similar_products:
                if similarities_for_idx[similar_idx] > self.threshold and merged_data.iloc[similar_idx]['site_id'] != \
                        row['site_id']:
                    similar_site_id = merged_data.iloc[similar_idx]['site_id']
                    if similar_site_id not in site_ids_seen:
                        site_ids_seen.add(similar_site_id)
                        results.append((row['id'], merged_data.iloc[similar_idx]['id']))
        result_df = pd.DataFrame(results, columns=['id_x', 'id_y'])
        return result_df

    @staticmethod
    def save_matches_to_file(result, merged_data, file_path='matched_products.txt'):
        with open(file_path, 'w', encoding='utf-8') as f:
            for _, row in result.iterrows():
                id_x, id_y = row['id_x'], row['id_y']
                product_x = merged_data.loc[merged_data['id'] == id_x, 'product'].values[0]
                product_y = merged_data.loc[merged_data['id'] == id_y, 'product'].values[0]
                f.write(f"Product 1: {product_x} (ID: {id_x}) - Product 2: {product_y} (ID: {id_y})\n")

    async def find_matches_products(self):
        products: list[Product] = await self.orm.product_repo.select_all()
        df_site = pd.DataFrame([(p.id, p.name, p.category.site_id) for p in products],
                               columns=['id', 'product', 'site_id'])
        merged_data = self.preprocess_products(df_site)
        similarities = self.find_similarities(merged_data)
        result = self.create_result_df(merged_data, similarities)
        self.save_matches_to_file(result, merged_data)
        await self.orm.general_product_repo.insert_or_update_general_products(result)

    async def loop_general_product(self):
        while True:
            await self.find_matches_products()
            time.sleep(self.orm.settings.timer)
