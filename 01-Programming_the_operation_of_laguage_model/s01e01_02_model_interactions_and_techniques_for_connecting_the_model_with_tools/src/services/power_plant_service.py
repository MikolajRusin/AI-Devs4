from ..utils.haversine_distance import haversine_distance

import json
import math

def load_power_plant_data(data_path: str) -> dict:
    with open(data_path, 'r', encoding='utf-8') as file:
        power_plant_data = json.load(file)
    return power_plant_data

def find_nearest_power_plant(power_plants: dict[str, str | dict[str, float]], person_locations: list[dict[str, float]]) -> dict[str, float]:
    nearest_power_plant = {
        'code': 'xxxxxxxx',
        'distance': math.inf
    }
    for _, power_plant_info in power_plants.items():
        curr_power_plant_location = power_plant_info['location']
        for curr_location in person_locations:
            distance = haversine_distance(
                (curr_power_plant_location['longitude'], curr_power_plant_location['latitude']),
                (curr_location['longitude'], curr_location['latitude']),
            )
            if distance < nearest_power_plant['distance']:
                nearest_power_plant['code'] = power_plant_info['code']
                nearest_power_plant['distance'] = distance
    
    return nearest_power_plant