from pathlib import Path
import requests

APP_ROOT = Path(__file__).parents[1]
DATA_DIR = APP_ROOT / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_data_from_url(url: str) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    dest_path = DATA_DIR / 'data.csv'
    with open(dest_path, 'wb') as f:
        f.write(response.content)

    print(f'The data has been saved as {dest_path}')
    return dest_path
