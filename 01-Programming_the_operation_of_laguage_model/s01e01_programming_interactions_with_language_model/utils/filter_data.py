import pandas as pd

def filter_gender(data_df: pd.DataFrame, gender: str) -> pd.DataFrame:
    return data_df[data_df['gender'] == gender]

def filter_city(data_df: pd.DataFrame, city: str) -> pd.DataFrame:
    return data_df[data_df['birthPlace'] == city]

def filter_age_between(
    data_df: pd.DataFrame,
    lower_bound: int,
    upper_bound: int,
) -> pd.DataFrame:
    data_df = (
        data_df
        .assign(
            born_year = lambda x: pd.to_datetime(x['birthDate'], format='%Y-%m-%d').dt.year,
            age = lambda x: pd.Timestamp('now').year - x['born_year']
        )
        .query(f'age >= {lower_bound} & age <= {upper_bound}')
        .drop('age', axis=1)
    )
    return data_df
