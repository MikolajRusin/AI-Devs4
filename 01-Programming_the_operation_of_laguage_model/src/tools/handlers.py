from ..clients.hub import AiDevsHubClient
from ..clients.openrouter_client import create_chat_completion
from ..prompts.tag_jobs import build_tag_jobs_prompt
from ..utils.create_batch import create_batch
from ..resources.job_tags import id2job_tag
from ..services.people_service import (
    load_people_data, filter_age_between, filter_city, filter_gender,
    attach_job_ids, select_people_by_tag
)
from ..services.power_plant_service import (
    load_power_plant_data
)


from pathlib import Path
import json


# ---- PEOPLE HANDLERS ----
def download_people_data(
    hub_client: AiDevsHubClient, 
    hub_api_key: str, 
    dest_dir: str | Path
) -> dict[str, str]:
    return {
        'people_data_path': hub_client.download_people_data(hub_api_key, dest_dir)
    }


def filter_people(
    people_data_path: str, 
    gender: str, 
    city: str, 
    lower_age_bound: int, 
    upper_age_bound: int
) -> dict[str, list[str | int] | int]:
    data_df = load_people_data(people_data_path)
    filtered_data = filter_gender(data_df, gender=gender)
    filtered_data = filter_city(filtered_data, city=city)
    filtered_data = filter_age_between(filtered_data, lower_bound=lower_age_bound, upper_bound=upper_age_bound)

    people_data_path = Path(people_data_path)
    filtered_people_path = people_data_path.parent / 'filtered_people.csv'
    filtered_data.to_csv(filtered_people_path, index=False)

    return {
        'filtered_people_path': str(filtered_people_path),
        'total_number_people': len(filtered_data)
    }


def tag_jobs(
    filtered_people_path: str,
    openrouter_api_key: str,
    openrouter_base_url: str,
    id_to_tag: dict[int, dict[str, str]],
    batch_size: int = 10
) -> dict[str, list[str]]:
    filtered_data_df = load_people_data(filtered_people_path)
    filtered_data_df, id_to_job_description = attach_job_ids(filtered_data_df)
    
    tagged_jobs: dict[str, list[str]] = {}
    for batch in create_batch(id_to_job_description, batch_size=batch_size):
        prompt_data = build_tag_jobs_prompt(batch, id_to_tag)
        response = create_chat_completion(
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
            model=prompt_data['metadata']['model_config']['model'],
            messages=[
                {'role': 'system', 'content': prompt_data['system_message']},
                {'role': 'user', 'content': prompt_data['user_message']},
            ],
            response_format=prompt_data['metadata']['response_format'],
        )
        content = response['choices'][0]['message']['content']
        parsed = json.loads(content)
        tagged_jobs.update(
            {
                job_id: [int(tag_id) for tag_id in tag_ids] 
                for job_id, tag_ids in parsed['tagged_jobs'].items()
            }
        )

    filtered_data_df.to_csv(filtered_people_path, index=False)

    data_dir = Path(filtered_people_path).parent
    tagged_jobs_path = data_dir / 'tagged_jobs.json'
    with open(tagged_jobs_path, 'w') as f:
        json.dump(tagged_jobs, f, indent=4)

    return {
        'filtered_people_path': str(filtered_people_path),
        'tagged_jobs_path': str(tagged_jobs_path)
    }


def get_job_tags() -> dict[int, str]:
    return {tag_id: job_desc['name'] for tag_id, job_desc in id2job_tag.items()}


def filter_people_by_job_tag_id(
    filtered_people_path: str,
    tagged_jobs_path: str,
    tag_id: int
) -> dict:
    filtered_data_df = load_people_data(filtered_people_path)
    with open(tagged_jobs_path, 'r', encoding='utf-8') as file:
        tagged_jobs = json.load(file)
    
    filtered_data_df = select_people_by_tag(
        filtered_data_df,
        tagged_jobs,
        tag_id
    )
    filtered_data_df.to_csv(filtered_people_path, index=False)
    
    return {
        'filtered_people_path': str(filtered_people_path)
    }


# ---- POWER PLANT HANDLERS ----
def download_power_plant_locations(
    hub_client: AiDevsHubClient, 
    hub_api_key: str, 
    dest_dir: str | Path
) -> dict[str, str]:
    power_plant_data_path = hub_client.download_power_plant_data(hub_api_key, dest_dir)
    power_plant_data = load_power_plant_data(power_plant_data_path)