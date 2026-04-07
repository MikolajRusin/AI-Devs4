import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'


@dataclass(frozen=True)
class SearchDataset:
    cities_df: pd.DataFrame
    items_df: pd.DataFrame
    full_df: pd.DataFrame


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\w+', str(text).lower())


@lru_cache(maxsize=1)
def load_data() -> SearchDataset:
    cities_df = pd.read_csv(DATA_DIR / 'cities.csv')
    items_df = pd.read_csv(DATA_DIR / 'items.csv')
    connections_df = pd.read_csv(DATA_DIR / 'connections.csv')

    full_df = (
        connections_df
        .merge(cities_df, left_on='cityCode', right_on='code', how='left')
        .merge(items_df, left_on='itemCode', right_on='code', how='left', suffixes=('_city', '_item'))
        .rename(columns={'name_city': 'city_name', 'name_item': 'item_name'})
        [['city_name', 'item_name']]
        .dropna()
        .drop_duplicates()
    )

    cities_df = cities_df.copy()
    items_df = items_df.copy()
    full_df = full_df.copy()

    return SearchDataset(
        cities_df=cities_df,
        items_df=items_df,
        full_df=full_df,
    )


def find_city_matches(query: str, dataset: SearchDataset | None = None) -> list[str]:
    data = dataset or load_data()
    city_query = str(query).strip()
    if not city_query:
        return []

    mask = data.cities_df['name'].str.contains(re.escape(city_query), regex=True, na=False)
    exact_or_inverse = data.cities_df['name'].map(
        lambda value: city_query in value or value in city_query
    )
    matches = data.cities_df.loc[mask | exact_or_inverse, 'name'].drop_duplicates().tolist()
    return sorted(matches, key=len)


def search_items(query: str, dataset: SearchDataset | None = None, limit: int = 12) -> list[str]:
    data = dataset or load_data()
    item_query = str(query).strip()
    if not item_query:
        return []

    items_df = data.items_df
    lower_query = item_query.lower()
    exact_matches = (
        items_df.loc[items_df['name'].str.lower().str.contains(re.escape(lower_query), regex=True, na=False), 'name']
        .drop_duplicates()
        .sort_values()
        .head(limit)
        .tolist()
    )
    if exact_matches:
        return exact_matches

    query_tokens = [token for token in _tokenize(item_query) if len(token) > 1]
    if not query_tokens:
        return []

    scored_df = items_df.copy()
    scored_df['match_score'] = scored_df['name'].fillna('').map(
        lambda value: sum(token in value.lower() for token in query_tokens)
    )
    scored_df = scored_df.loc[scored_df['match_score'] > 0, ['name', 'match_score']]
    if scored_df.empty:
        return []

    min_score = 2 if len(query_tokens) >= 2 else 1
    filtered_df = scored_df.loc[scored_df["match_score"] >= min_score]
    if filtered_df.empty:
        filtered_df = scored_df

    return (
        filtered_df
        .drop_duplicates(subset=['name'])
        .sort_values(by=['match_score', 'name'], ascending=[False, True])
        .head(limit)['name']
        .tolist()
    )


def cities_for_item_queries(
    item_queries: Iterable[str],
    dataset: SearchDataset | None = None,
) -> dict[str, list[str]]:
    data = dataset or load_data()
    results: dict[str, list[str]] = {}

    for query in item_queries:
        matched_items = search_items(query, data, limit=20)
        if not matched_items:
            continue

        cities = (
            data.full_df.loc[data.full_df['item_name'].isin(matched_items), 'city_name']
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        if cities:
            results[query] = cities
    return results


def items_in_city(city_name: str, dataset: SearchDataset | None = None) -> list[str]:
    data = dataset or load_data()
    matched_cities = find_city_matches(city_name, data)
    if not matched_cities:
        return []

    return (
        data.full_df.loc[data.full_df['city_name'] == matched_cities[0], 'item_name']
        .drop_duplicates()
        .sort_values()
        .tolist()
    )


def intersection_for_item_queries(
    item_queries: Iterable[str],
    dataset: SearchDataset | None = None,
) -> list[str]:
    queries = list(item_queries)
    per_query = cities_for_item_queries(queries, dataset)
    city_sets = [set(city_names) for city_names in per_query.values() if city_names]
    if not city_sets or len(city_sets) != len(queries):
        return []
    return sorted(set.intersection(*city_sets))
