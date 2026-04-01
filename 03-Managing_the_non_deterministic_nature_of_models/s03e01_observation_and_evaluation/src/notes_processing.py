import pandas as pd
import json
from typing import Any

from .chat_client import chat_responses
from .build_prompt import build_classify_note_fragment_prompt


def get_notes_groups_and_fragments(df: pd.DataFrame) -> tuple[dict[str, list[str]], list[str]]:
    notes_groups = df[['operator_notes']].groupby('operator_notes').groups
    note_fragments = list(set({note_fragment for group in notes_groups for note_fragment in group.split(', ')}))
    return notes_groups, note_fragments

def _extract_output_message(output_items: list[dict]) -> dict[str, Any]:
    for item in output_items:
        if item.get('type') == 'message':
            return item
    return []

def classify_note_fragments(note_fragments: list[str]) -> dict[int, str]:
    id_to_note_fragment = dict(zip(range(len(note_fragments)), note_fragments))

    prompt = build_classify_note_fragment_prompt(id_to_note_fragment)
    response = chat_responses(
        model=prompt['metadata']['model_config']['model'],
        input=[
            {'role': 'user', 'content': prompt['user_message']}
        ],
        instructions=prompt['instructions'],
        response_format=prompt['metadata']['response_format']
    )

    output_message = _extract_output_message(response['output'])
    if not output_message:
        return 'No response received'

    text = json.loads(output_message['content'][0]['text'])
    note_fragment_classification = text['note_fragment_classification']

    classified_fragments = {id_to_note_fragment[object['id']]: object['label'] for object in note_fragment_classification}
    return classified_fragments