from ..clients.hub import AiDevsHubClient
from ..clients.llm_router import LlmResponseFn
from ..prompts.tag_jobs import build_tag_jobs_prompt
from ..prompts.find_power_plant_location import build_find_power_plant_location_prompt
from ..utils.create_batch import create_batch
from ..resources.job_tags import id2job_tag
from ..services.people_service import (
    load_people_data, filter_age_between, filter_city, filter_gender,
    attach_job_ids, select_people_by_tag
)
from ..services.power_plant_service import (
    load_power_plant_data, find_nearest_power_plant
)

from pathlib import Path
import json


def get_parsed_llm_response(prompt_data: dict, get_llm_response: LlmResponseFn) -> dict:
    raw_response = get_llm_response(
        model=prompt_data['metadata']['model_config']['model'],
        messages=[
            {'role': 'system', 'content': prompt_data['system_message']},
            {'role': 'user', 'content': prompt_data['user_message']},
        ],
        response_format=prompt_data['metadata']['response_format']
    )
    return json.loads(raw_response['choices'][0]['message']['content'])


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
    id_to_tag: dict[int, dict[str, str]],
    get_llm_response: LlmResponseFn,
    batch_size: int = 10
) -> dict[str, list[str]]:
    filtered_data_df = load_people_data(filtered_people_path)
    filtered_data_df, id_to_job_description = attach_job_ids(filtered_data_df)
    
    tagged_jobs: dict[str, list[str]] = {}
    for batch in create_batch(id_to_job_description, batch_size=batch_size):
        prompt_data = build_tag_jobs_prompt(batch, id_to_tag)
        response = get_parsed_llm_response(prompt_data, get_llm_response)
        tagged_jobs.update(
            {
                item['job_id']: [int(tag_id) for tag_id in item['tag_ids']] 
                for item in response['tagged_jobs']
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
    get_llm_response: LlmResponseFn,
    dest_dir: str | Path
) -> dict[str, str]:
    power_plant_data_path = hub_client.download_power_plant_data(hub_api_key, dest_dir)
    power_plant_data = load_power_plant_data(power_plant_data_path)

    power_plants_dict = {
        city_name: power_plant_info['code'] 
        for city_name, power_plant_info in power_plant_data['power_plants'].items()
    }
    prompt_data = build_find_power_plant_location_prompt(power_plants_dict)
    response = get_parsed_llm_response(prompt_data, get_llm_response)
    locations = {
        item['power_plant_code']: {
            'longitude': item['longitude'],
            'latitude': item['latitude']
        }
        for item in response['power_plant_locations']
    }

    for power_plant in power_plant_data['power_plants'].values():
        power_plant['location'] = locations.get(power_plant['code'], {})
    
    with open(power_plant_data_path, 'w') as file:
        json.dump(power_plant_data, file, indent=4)
    return {
        'power_plant_data_path': power_plant_data_path
    }

def identify_power_plant_suspect(
    power_plant_data_path: str,
    filtered_people_path: str,
    hub_client: AiDevsHubClient,
    hub_api_key: str
) -> dict:
    people_df = load_people_data(filtered_people_path)
    power_plant_json = load_power_plant_data(power_plant_data_path)

    person_nearest_power_plant = {
        'power_plant_code': [],
        'distance': []
    }
    for _, person in people_df.iterrows():
        person_locations = hub_client.get_person_locations(
            api_key=hub_api_key, 
            name=person['name'],
            surname=person['surname']
        )
        nearest_power_plant = find_nearest_power_plant(power_plant_json['power_plants'], person_locations)
        person_nearest_power_plant['power_plant_code'].append(nearest_power_plant['code'])
        person_nearest_power_plant['distance'].append(nearest_power_plant['distance'])
    
    people_df['power_plant_code'] = person_nearest_power_plant['power_plant_code']
    people_df['distance'] = person_nearest_power_plant['distance']
    people_df.to_csv(Path(filtered_people_path).parent / 'filtered_people_with_code.csv', index=False)

    suspect = people_df.loc[people_df['distance'].idxmin()]

    return {
        'name': suspect['name'],
        'surname': suspect['surname'],
        'birth_date': suspect['birthDate'],
        'power_plant_code': suspect['power_plant_code'],
    }

def get_access_level(
    name: str,
    surname: str,
    birth_year: int,
    hub_client: AiDevsHubClient, 
    hub_api_key: str,
) -> dict:
    return hub_client.get_person_access_level(
        api_key=hub_api_key, 
        name=name,
        surname=surname,
        birth_year=birth_year
    )

def send_message(
    name: str, 
    surname: str, 
    access_level: int, 
    power_plant_code: str,
    message_header: str,
    hub_client: AiDevsHubClient, 
    hub_api_key: str,
) -> dict:
    answer = {
        'name': name,
        'surname': surname,
        'accessLevel': access_level,
        'powerPlant': power_plant_code
    }
    response = hub_client.verify_answer(
        api_key=hub_api_key,
        task_name=message_header,
        answer=answer
    )
    return response