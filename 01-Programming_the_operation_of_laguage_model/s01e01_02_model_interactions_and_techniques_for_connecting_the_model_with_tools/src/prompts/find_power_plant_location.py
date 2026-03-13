from jinja2 import Template
from pathlib import Path
import frontmatter

APP_ROOT = Path(__file__).parents[1]
TEMPLATE_PATH = APP_ROOT / 'prompt_templates' / 'find_power_plant_location_prompt.md'


def build_find_power_plant_location_prompt(
    power_plants_dict: dict[str, str]
) -> dict:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    template = Template(post.content)
    content = template.render(
        power_plants_dict=power_plants_dict,
    )

    parts = content.split('# Input Data', maxsplit=1)
    if len(parts) != 2:
        raise ValueError('Prompt template must contain a "# Input Data" section.')

    system_part = parts[0].strip()
    user_part = f'# Input Data\n{parts[1].strip()}'

    return {
        'system_message': system_part,
        'user_message': user_part,
        'metadata': post.metadata
    }
