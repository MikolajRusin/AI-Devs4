import json
from typing import Any, Literal
from pathlib import Path

from ..clients.hub_client import AiDevsHubClient
from ..services.board_service import download_board, load_image, encode_image_to_base64, crop_board, rotate_tile
from ..services.board_vision import build_image_url, run_vision
from ..prompts.board_description import build_board_description_prompt
from ..config import BoardSettings


IMAGE_MIME_TYPES = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp'
}

def load_board(
    board_type: Literal['current', 'solved'],
    hub_client: AiDevsHubClient,
    board_settings: BoardSettings,
    llm_client
) -> dict[str, Any]:
    board_path   = download_board(hub_client, board_type)
    board_image  = load_image(board_path)
    board_image  = crop_board(board_image, **board_settings.model_dump())
    image_base64 = encode_image_to_base64(board_image, Path(board_path).name)
    image_url    = build_image_url(image_base64, IMAGE_MIME_TYPES[Path(board_path).suffix])
    
    prompt = build_board_description_prompt(individual_tile=False)
    
    vision_response = run_vision(
        image_url=image_url, 
        query=prompt['user_prompt'],
        system_prompt=prompt['system_prompt'],
        model=prompt['model_config']['model'],
        response_format=prompt['response_format'],
        llm_response_client=llm_client,
    )
    return json.loads(vision_response['choices'][0]['message']['content'])

def load_one_tile(
    board_type: Literal['current', 'solved'],
    row: int,
    column: int,
    hub_client: AiDevsHubClient,
    board_settings: BoardSettings,
    llm_client
) -> dict[str, Any]:
    board_path   = download_board(hub_client, board_type)
    board_image  = load_image(board_path)
    board_image  = crop_board(board_image, **board_settings.model_dump())
    board_image  = crop_board(board_image, (column-1) * 95, (row-1) * 96, 100, 100)
    image_base64 = encode_image_to_base64(board_image, Path(board_path).name)
    image_url    = build_image_url(image_base64, IMAGE_MIME_TYPES[Path(board_path).suffix])

    prompt = build_board_description_prompt(individual_tile=True)
    
    vision_response = run_vision(
        image_url=image_url, 
        query=prompt['user_prompt'],
        system_prompt=prompt['system_prompt'],
        model=prompt['model_config']['model'],
        response_format=prompt['response_format'],
        llm_response_client=llm_client,
    )
    response_dict = json.loads(vision_response['choices'][0]['message']['content'])
    return {
        f'{row}x{column}': sorted(response_dict['exits'])
    }

def rotate_one_tile(
    row: int,
    column: int,
    hub_client: AiDevsHubClient
) -> dict[str, Any]:
    return rotate_tile(row, column, hub_client)