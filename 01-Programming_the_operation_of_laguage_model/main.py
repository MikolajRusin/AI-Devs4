import s01e01_programming_interactions_with_language_model as s01e01
from s01e01_programming_interactions_with_language_model.agents.job_tagger import JobTagger
from s01e01_programming_interactions_with_language_model.config.job_tags import id2tag
from s01e01_programming_interactions_with_language_model.config.settings import (
    PeopleFilterCriteria,
    Settings,
)
from s01e01_programming_interactions_with_language_model.clients.hub import AiDevsHubClient
from s01e01_programming_interactions_with_language_model.pipeline.people_pipeline import (
    attach_job_ids,
    build_people_answer,
    collect_job_tags,
    filter_people,
    get_tag_id_by_name,
    select_people_by_tag,
)
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

load_dotenv()
PACKAGE_ROOT = Path(__file__).parent
DATA_DIR = PACKAGE_ROOT / 's01e01_programming_interactions_with_language_model' / 'data'
DATA_PATH = DATA_DIR / 'data.csv'


def build_filter_criteria() -> PeopleFilterCriteria:
    return PeopleFilterCriteria(
        gender='M',
        city='Grudziądz',
        min_age=20,
        max_age=40,
    )


def create_clients(settings: Settings) -> tuple[AiDevsHubClient, JobTagger]:
    hub_client = AiDevsHubClient(base_url=settings.hub_base_url)
    job_tagger = JobTagger(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        id_to_tag=id2tag,
    )
    return hub_client, job_tagger


def prepare_answer(
    settings: Settings,
    hub_client: AiDevsHubClient,
    job_tagger: JobTagger,
) -> list[dict]:
    batch_size = 10
    selected_tag_name = 'transport'
    
    criteria = build_filter_criteria()
    transport_tag_id = get_tag_id_by_name(id2tag, selected_tag_name)

    data_path = hub_client.download_people_data(settings.ai_devs_hub_api_key, DATA_PATH)
    data_df = pd.read_csv(data_path)

    filtered_people = filter_people(data_df, criteria)
    people_with_job_ids, id_to_job_description = attach_job_ids(filtered_people)

    tagged_jobs = collect_job_tags(
        id_to_job_description=id_to_job_description,
        job_tagger=job_tagger,
        batch_size=batch_size,
    )
    transport_people = select_people_by_tag(
        data_df=people_with_job_ids,
        tagged_jobs=tagged_jobs,
        selected_tag_id=transport_tag_id,
    )
    return build_people_answer(transport_people, tagged_jobs, id2tag)


def main() -> None:
    settings = Settings.from_env()
    hub_client, job_tagger = create_clients(settings)
    prepared_answer = prepare_answer(settings, hub_client, job_tagger)

    print(f'Number of people: {len(prepared_answer)}')
    print(prepared_answer)

    verification_response = hub_client.verify_people_answer(
        api_key=settings.ai_devs_hub_api_key,
        task_name=settings.people_task_name,
        answer=prepared_answer,
    )
    print(verification_response)

if __name__ == '__main__':
    main()
