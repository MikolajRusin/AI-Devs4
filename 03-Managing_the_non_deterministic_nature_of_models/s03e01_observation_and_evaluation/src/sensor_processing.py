import json
import glob
from pathlib import Path

import pandas as pd

SENSOR2METRIC = {
    'temperature': 'temperature_K',
    'pressure': 'pressure_bar',
    'water': 'water_level_meters',
    'voltage': 'voltage_supply_v',
    'humidity': 'humidity_percent'
}

VALID_RANGES = {
    'temperature_K': (553, 873),
    'pressure_bar': (60, 160),
    'water_level_meters': (5.0, 15.0),
    'voltage_supply_v': (229.0, 231.0),
    'humidity_percent': (40.0, 80.0)
}

def load_sensor_data(dir_path: str | Path) -> pd.DataFrame:
    json_pattern = str(Path(dir_path) / '*.json')
    file_list = glob.glob(json_pattern)

    records = []
    for file in file_list:
        with open(file, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
        
        json_file['file_id'] = Path(file).stem
        records.append(json_file)
    
    df = pd.DataFrame(records)
    df = df.set_index('file_id')
    return df

def validate_sensor_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df
        .assign(
            expected_columns=lambda d: d['sensor_type'].str.split('/').apply(lambda sensors: [SENSOR2METRIC[s] for s in sensors])
        )
        .assign(
            unexpected_metric=lambda d: d.apply(
                lambda row: any(row[col] != 0 for col in SENSOR2METRIC.values() if col not in row['expected_columns']), 
                axis=1
            ),
            out_of_range=lambda d: d.apply(
                lambda row: any((row[col] < VALID_RANGES[col][0]) or (row[col] > VALID_RANGES[col][1]) for col in row['expected_columns']), 
                axis=1
            )
        )
        .assign(
            sensor_metrics_ok=lambda d: ~(d['unexpected_metric'] | (d['out_of_range']))
        )
    )
