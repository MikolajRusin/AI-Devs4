import pandas as pd

from ..config.settings import PeopleFilterCriteria
from ..utils.create_batch import create_batch
from ..utils.filter_data import filter_age_between, filter_city, filter_gender


def get_tag_id_by_name(
    id_to_tag: dict[int, dict[str, str]],
    tag_name: str,
) -> str:
    for tag_id, tag_info in id_to_tag.items():
        if tag_info['name'] == tag_name:
            return str(tag_id)
    raise ValueError(f'Could not find tag ID for tag name: {tag_name}')


def filter_people(data_df: pd.DataFrame, criteria: PeopleFilterCriteria) -> pd.DataFrame:
    filtered = filter_gender(data_df, gender=criteria.gender)
    filtered = filter_city(filtered, city=criteria.city)
    filtered = filter_age_between(
        filtered,
        lower_bound=criteria.min_age,
        upper_bound=criteria.max_age,
    )
    return filtered.copy()


def attach_job_ids(data_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, str]]:
    unique_jobs = data_df['job'].dropna().unique().tolist()
    id_to_job_description = dict(enumerate(unique_jobs))
    job_description_to_id = {
        job_description: job_id
        for job_id, job_description in id_to_job_description.items()
    }

    prepared_df = data_df.copy()
    prepared_df['job_id'] = prepared_df['job'].map(job_description_to_id)
    return prepared_df, id_to_job_description


def collect_job_tags(
    id_to_job_description: dict[int, str],
    job_tagger,
    batch_size: int,
) -> dict[str, list[str]]:
    tagged_jobs: dict[str, list[str]] = {}

    for batch in create_batch(id_to_job_description, batch_size=batch_size):
        batch_results = job_tagger.tag_jobs(batch)
        tagged_jobs.update(batch_results)

    return tagged_jobs


def select_people_by_tag(
    data_df: pd.DataFrame,
    tagged_jobs: dict[str, list[str]],
    selected_tag_id: str,
) -> pd.DataFrame:
    selected_job_ids = {
        int(job_id)
        for job_id, tag_ids in tagged_jobs.items()
        if selected_tag_id in tag_ids
    }
    return data_df[data_df['job_id'].isin(selected_job_ids)].copy()


def build_people_answer(
    data_df: pd.DataFrame,
    tagged_jobs: dict[str, list[str]],
    id_to_tag: dict[int, dict[str, str]],
) -> list[dict]:
    answer = []

    for row in data_df.to_dict(orient='records'):
        job_tags = tagged_jobs[str(row['job_id'])]
        answer.append(
            {
                'name': row['name'],
                'surname': row['surname'],
                'gender': row['gender'],
                'born': int(row['born_year']),
                'city': row['birthPlace'],
                'tags': [id_to_tag[int(tag_id)]['name'] for tag_id in job_tags],
            }
        )

    return answer
