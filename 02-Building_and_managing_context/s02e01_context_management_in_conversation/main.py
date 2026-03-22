from utils.config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL
from typing import Iterator, Any
from jinja2 import Template
from pathlib import Path
import frontmatter
import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
TEMPLATE_PATH = PROJECT_ROOT / 'utils' / 'prompt_template.md'

def download_data(destination_dir: str | Path) -> str:
    file_name = 'categorize.csv'
    url = f'{AI_DEVS_HUB_BASE_URL}/data/{AI_DEVS_HUB_API_KEY}/{file_name}'
    response = requests.get(url=url, timeout=30)
    response.raise_for_status()

    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    dest_path = destination_dir / file_name
    dest_path.write_text(response.text, encoding='utf-8')

    return str(dest_path)

def load_data_rows(data_path: str | Path) -> Iterator[dict[str, str]]:
    df = pd.read_csv(Path(data_path))

    for _, row in df.iterrows():
        yield {
            'part_code': str(row['code']),
            'part_desc': str(row['description']),
        }

def build_part_classification_prompt(part_code: str, part_description: str) -> str:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    template = Template(post.content)
    content = template.render(
        code=part_code,
        description=part_description
    )
    return content

def send_prompt(prompt: str) -> dict[str, Any]:
    url=f'{AI_DEVS_HUB_BASE_URL}/verify'
    response = requests.post(
        url=url,
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'task': 'categorize',
            'answer': {
                'prompt': prompt
            }
        }
    )
    return response.json()

def main():
    data_path = download_data(DATA_DIR)
    for part in load_data_rows(data_path):
        prompt = build_part_classification_prompt(part['part_code'], part['part_desc'])
        hub_response = send_prompt(prompt)
        print(hub_response)

    reset_response = send_prompt('reset')
    print(reset_response)

if __name__ == '__main__':
    main()