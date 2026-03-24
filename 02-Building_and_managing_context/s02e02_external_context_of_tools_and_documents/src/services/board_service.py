import cv2
import base64
import numpy as np
from pathlib import Path
from typing import Literal, Any

from ..clients.hub_client import AiDevsHubClient


def download_board(hub_client: AiDevsHubClient, board: Literal['current', 'solved'] = False) -> str:
    return hub_client.download_board_image(board)

def load_image(img_path: str | Path) -> np.ndarray:
    img = cv2.imread(str(img_path))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def encode_image_to_base64(image: np.ndarray, file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    success, buffer = cv2.imencode(suffix, image)
    if not success:
        raise ValueError('Failed to encode image')

    return base64.b64encode(buffer.tobytes()).decode('utf-8')

def crop_board(img_board: np.ndarray, x_min: int | float, y_min: int | float, width: int | float, height: int | float) -> np.ndarray:
    return img_board[y_min:y_min + height, x_min:x_min + width]

def rotate_tile(row: int, column: int, hub_client: AiDevsHubClient) -> dict[str, Any]:
    return hub_client.rotate_cable(f'{row}x{column}')