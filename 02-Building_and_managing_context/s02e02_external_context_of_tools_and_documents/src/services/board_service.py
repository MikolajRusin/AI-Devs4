import cv2
import numpy as np
from pathlib import Path

from ..config import BoardSettings
from ..clients.hub_client import AiDevsHubClient


def download_board(hub_client: AiDevsHubClient, final_board: bool = False) -> str:
    return hub_client.download_board_image(final_board)

def load_board(img_board_path: str | Path) -> np.ndarray:
    img = cv2.imread(img_board_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def crop_board(img_board: np.ndarray, x_min: int | float, y_min: int | float, width: int | float, height: int | float) -> str:
    return img_board[y_min:y_min + width, x_min:x_min + height]