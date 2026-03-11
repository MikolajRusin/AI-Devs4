import json

def load_power_plant_data(data_path: str) -> dict:
    with open(data_path, 'r', encoding='utf-8') as file:
        power_plant_data = json.load(file)
    return power_plant_data