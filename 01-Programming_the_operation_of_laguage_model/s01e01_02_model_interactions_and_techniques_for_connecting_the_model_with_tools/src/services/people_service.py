import pandas as pd
import json


def load_people_data(data_path: str) -> pd.DataFrame:
    return pd.read_csv(data_path)

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
            age = lambda x: pd.Timestamp('now').year - pd.to_datetime(x['birthDate'], format='%Y-%m-%d').dt.year
        )
        .query(f'age >= {lower_bound} & age <= {upper_bound}')
        .drop('age', axis=1)
    )
    return data_df

def attach_job_ids(data_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, str]]:
    unique_jobs = data_df['job'].unique().tolist()
    id_to_job_description = dict(enumerate(unique_jobs))
    job_description_to_id = {
        job_description: job_id
        for job_id, job_description in id_to_job_description.items()
    }

    prepared_df = data_df.copy()
    prepared_df['job_id'] = prepared_df['job'].map(job_description_to_id)
    return prepared_df, id_to_job_description

def select_people_by_tag(
    data_df: pd.DataFrame,
    tagged_jobs: dict[str, list[int]],
    selected_tag_id: int,
) -> pd.DataFrame:
    selected_job_ids = {
        int(job_id)
        for job_id, tag_ids in tagged_jobs.items()
        if selected_tag_id in tag_ids
    }
    return data_df[data_df['job_id'].isin(selected_job_ids)].copy()
