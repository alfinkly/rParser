import logging
import time

import nltk as nltk
import numpy as np
import pandas as pd
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.database import ORM


class ProductMatcher:
    def __init__(self, orm: ORM):
        nltk.download('stopwords')
        nltk.download('wordnet')
        self.orm = orm
        self.custom_stop_words = {'select', 'arbuz'}
        self.threshold = 0.8

    async def fetch_products(self, site_id):
        return await self.orm.product_repo.select_site_products(site_id)

    @staticmethod
    def products_to_df(products, site_id):
        return pd.DataFrame([(p.id, p.name, site_id) for p in products], columns=['id', 'product', 'site_id'])

    def normalize_string(self, s):
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('russian'))
        stop_words.update(self.custom_stop_words)
        words = ''.join(e for e in s if e.isalnum() or e.isspace()).lower().split()
        return ' '.join(lemmatizer.lemmatize(word) for word in words if word not in stop_words)

    def preprocess_products(self, merged_data):
        merged_data['product_norm'] = merged_data['product'].apply(self.normalize_string)
        return merged_data

    def find_similarities(self, merged_data):
        vectorizer = TfidfVectorizer().fit_transform(merged_data['product_norm'])
        cosine_similarities = cosine_similarity(vectorizer)
        matches = np.argwhere(cosine_similarities > self.threshold)
        return matches

    @staticmethod
    def create_result_df(merged_data, matches):
        result = pd.DataFrame(matches, columns=['id_x', 'id_y'])
        result = result[result['id_x'] != result['id_y']].drop_duplicates()
        result['id_x'] = merged_data.iloc[result['id_x']]['id'].values
        result['id_y'] = merged_data.iloc[result['id_y']]['id'].values
        return result

    @staticmethod
    def save_matches_to_file(result, merged_data, file_path='matched_products.txt'):
        with open(file_path, 'w', encoding='utf-8') as f:
            for _, row in result.iterrows():
                id_x, id_y = row['id_x'], row['id_y']
                product_x = merged_data.loc[merged_data['id'] == id_x, 'product'].values[0]
                product_y = merged_data.loc[merged_data['id'] == id_y, 'product'].values[0]
                f.write(f"Product 1: {product_x} (ID: {id_x}) - Product 2: {product_y} (ID: {id_y})\n")

    async def find_matches(self):
        while True:
            products_1 = await self.fetch_products(1)
            products_2 = await self.fetch_products(2)

            df_site1 = self.products_to_df(products_1, 1)
            df_site2 = self.products_to_df(products_2, 2)

            merged_data = pd.concat([df_site1, df_site2])
            merged_data = self.preprocess_products(merged_data)

            matches = self.find_similarities(merged_data)
            result = self.create_result_df(merged_data, matches)

            self.save_matches_to_file(result, merged_data)

            await self.orm.product_match_repo.insert_or_update_products_match(result)
            time.sleep(self.orm.settings.timer)
