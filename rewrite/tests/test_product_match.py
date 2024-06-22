import pytest
from unittest.mock import AsyncMock, Mock
import pandas as pd

from methods.find_matches import ProductMatcher


@pytest.fixture
def orm_mock():
    orm = Mock()
    orm.product_repo.select_all = AsyncMock(return_value=[
        Mock(id=1, name="Арбуз", category=Mock(site_id=1)),
        Mock(id=2, name="Кавун", category=Mock(site_id=2)),
    ])
    orm.product_match_repo.insert_or_update_products_match = AsyncMock()
    orm.settings = Mock(timer=1)
    return orm


@pytest.fixture
def product_matcher(orm_mock):
    return ProductMatcher(orm_mock)


@pytest.mark.asyncio
async def test_fetch_products(product_matcher):
    products = await product_matcher.fetch_products(1)
    assert len(products) == 2
    assert products[0].name == "Арбуз"


def test_products_to_df(product_matcher):
    products = [
        Mock(id=1, name="Арбуз", category=Mock(site_id=1)),
        Mock(id=2, name="Кавун", category=Mock(site_id=2)),
    ]
    df = product_matcher.products_to_df(products)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['id', 'product', 'site_id']


def test_normalize_string(product_matcher):
    result = product_matcher.normalize_string("Арбуз и Кавун")
    assert result == "арбуз кавун"


def test_preprocess_products(product_matcher):
    data = {
        'id': [1, 2],
        'product': ["Арбуз", "Кавун"],
        'site_id': [1, 2]
    }
    df = pd.DataFrame(data)
    processed_df = product_matcher.preprocess_products(df)
    assert 'product_norm' in processed_df.columns
    assert processed_df.loc[0, 'product_norm'] == "арбуз"
    assert processed_df.loc[1, 'product_norm'] == "кавун"


def test_find_similarities(product_matcher):
    data = {
        'id': [1, 2],
        'product': ["Арбуз", "Кавун"],
        'product_norm': ["арбуз", "кавун"],
        'site_id': [1, 2]
    }
    df = pd.DataFrame(data)
    matches = product_matcher.find_similarities(df)
    assert len(matches) > 0


def test_create_result_df(product_matcher):
    data = {
        'id': [1, 2],
        'product': ["Арбуз", "Кавун"],
        'product_norm': ["арбуз", "кавун"],
        'site_id': [1, 2]
    }
    df = pd.DataFrame(data)
    matches = product_matcher.find_similarities(df)
    result_df = product_matcher.create_result_df(df, matches)
    assert isinstance(result_df, pd.DataFrame)


def test_save_matches_to_file(product_matcher):
    data = {
        'id': [1, 2],
        'product': ["Арбуз", "Кавун"],
        'product_norm': ["арбуз", "кавун"],
        'site_id': [1, 2]
    }
    df = pd.DataFrame(data)
    matches = product_matcher.find_similarities(df)
    result_df = product_matcher.create_result_df(df, matches)
    file_path = "D:\PROJECTS\shoparsers\\rewrite\matched_products.txt"
    product_matcher.save_matches_to_file(result_df, df, file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        lenn = len(lines)
        assert lenn > 0


@pytest.mark.asyncio
async def test_find_matches_products(product_matcher):
    await product_matcher.find_matches_products()
    product_matcher.orm.product_match_repo.insert_or_update_products_match.assert_called()
