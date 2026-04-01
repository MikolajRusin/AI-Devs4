import re
import frontmatter
from pathlib import Path
from jinja2 import Template


TEMPLATE_PATH = Path(__file__).parent / 'classify_note_fragment_prompt_template.md'

def build_classify_note_fragment_prompt(
    id_to_note_fragment: dict[int, str],
) -> dict:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    template = Template(post.content)
    content = template.render(
        id_to_note_fragment=id_to_note_fragment,
    )

    role_match = re.search(r'<role>.*?</role>', content, flags=re.DOTALL)
    if not role_match:
        raise ValueError('Prompt template must contain a "<role>" section.')

    role_part = role_match.group(0).strip()
    rest_part = content.replace(role_part, '', 1).strip()

    return {
        'instructions': role_part,
        'user_message': rest_part,
        'metadata': post.metadata,
    }
