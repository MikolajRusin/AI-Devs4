import json
import requests
from pathlib import Path
from typing import Iterator, Any
from tqdm import tqdm

from src.sensor_processing import (
    load_sensor_data, validate_sensor_metrics
)
from src.notes_processing import ( 
    get_notes_groups_and_fragments, classify_note_fragments
)
from src.config import AI_DEVS_HUB_API_KEY, AI_DEVS_HUB_BASE_URL


ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / 'workspace' / 'sensor_data'


def create_batch(note_fragments: list[str], batch_size: int = 10) -> Iterator[list[str]]:
    batch = []
    for fragment in note_fragments:
        batch.append(fragment)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def send_anomalies(anomalies_ids: list[str]) -> dict[str, Any]:
    response = requests.post(
        url=f'{AI_DEVS_HUB_BASE_URL}/verify',
        json={
            'apikey': AI_DEVS_HUB_API_KEY,
            'task': 'evaluation',
            'answer': {
                'recheck': anomalies_ids
            }
        }
    )
    return response.json()

def main():
    df = load_sensor_data(DATA_DIR)
    df = validate_sensor_metrics(df)

    anomalies_ids = list(df[~df['sensor_metrics_ok']].index)
    df_valid = df[df['sensor_metrics_ok']].copy()

    notes_groups, note_fragments = get_notes_groups_and_fragments(df_valid)

    batch_size = 20
    classified_fragments = {}
    for batch in tqdm(create_batch(note_fragments, batch_size), total=len(note_fragments) // batch_size):
        classified_batch = classify_note_fragments(batch)
        classified_fragments.update(classified_batch)

    note_anomalies = {
        note: [classified_fragments[fragment] for fragment in note.split(', ')]
        for note in notes_groups
        if any(classified_fragments[fragment] == 'INVALID' for fragment in note.split(', '))
    }
    with open(str(DATA_DIR.parent / 'anomalies.json'), 'w') as f:
        json.dump(note_anomalies, f, indent=4)

    for note in note_anomalies.keys():
        anomalies_ids.extend(notes_groups[note])
    
    print(f'LEN ANOMALIES: {len(anomalies_ids)}')
    response = send_anomalies(anomalies_ids)
    print(response)

if __name__ == '__main__':
    main()