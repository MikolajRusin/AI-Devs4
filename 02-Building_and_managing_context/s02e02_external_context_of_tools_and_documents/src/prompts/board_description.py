from jinja2 import Template
from pathlib import Path
import frontmatter


APP_ROOT = Path(__file__).parents[1]
TEMPLATES_DIR = APP_ROOT / 'prompt_templates'
BOARD_DESCRIPTION_TEMPLATE_PATH = TEMPLATES_DIR / 'board_description_prompt.md'
INDIVIDUAL_TILE_TEMPLATE_PATH = TEMPLATES_DIR / 'individual_tile_description_prompt.md'


def _extract_section(content: str, start_tag: str, end_tag: str) -> str:
    return content.split(start_tag, 1)[1].split(end_tag, 1)[0].strip()


def build_board_description_prompt(individual_tile: bool = False) -> dict:
    template_path = INDIVIDUAL_TILE_TEMPLATE_PATH if individual_tile else BOARD_DESCRIPTION_TEMPLATE_PATH
    with open(template_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    template = Template(post.content)
    content  = template.render()

    system_prompt = _extract_section(content, '<SYSTEM_PROMPT>', '</SYSTEM_PROMPT>')
    user_prompt = _extract_section(content, '<USER_PROMPT>', '</USER_PROMPT>')

    return {
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'response_format': post.metadata.get('response_format'),
        'model_config': post.metadata.get('model_config'),
        'task': post.metadata.get('task'),
        'version': post.metadata.get('version'),
    }