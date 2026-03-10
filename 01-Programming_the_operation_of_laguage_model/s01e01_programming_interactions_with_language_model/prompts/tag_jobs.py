from jinja2 import Template
from pathlib import Path
import frontmatter

APP_ROOT = Path(__file__).parents[1]
TEMPLATE_PATH = APP_ROOT / 'prompt_templates' / 'tag_agent_prompt.md'


def build_tag_jobs_prompt(
    jobs_dict: dict[int, str],
    id2tag: dict[int, dict[str, str]],
) -> dict:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    template = Template(post.content)
    content = template.render(
        id2job_desc=jobs_dict,
        id2tag=id2tag
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
