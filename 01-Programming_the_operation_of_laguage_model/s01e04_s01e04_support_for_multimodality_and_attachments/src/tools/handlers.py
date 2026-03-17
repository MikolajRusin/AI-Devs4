from ..services.document_service import download_document, send_answer
from ..services.vision_ocr_service import run_document_ocr
from ..services.filesystem_service import (
    read_text_file, read_media_file,
    write_file, create_directory, list_directory, directory_tree
)
from ..clients.hub_client import AiDevsHubClient
from ..mcp.filesystem_client import MCPFileSystemClient
from ..utils.logger import logger

from typing import Literal, Any


async def download_documents(document_names: list[str], hub_client: AiDevsHubClient) -> dict[str, str]:
    logger.tool('download_documents', {'document_names': document_names})

    doc_data = {}
    for doc_name in document_names:
        doc_data[doc_name] = await download_document(doc_name, hub_client)
    return doc_data

FileType = Literal['text', 'media']
async def read_file(
    file_path: str, 
    file_type: FileType, 
    filesystem_client: MCPFileSystemClient, 
    mistral_api_key: str, 
    mistral_ocr_endpoint: str,
    mistral_ocr_model: str
) -> dict[str, str]:
    logger.tool('read_file', {'file_path': file_path, 'file_type': file_type})

    if file_type == 'text':
        text_result = await read_text_file(file_path, filesystem_client)

        if not text_result['ok']:
            logger.error(
                'Text file read failed',
                f'path={file_path} result={text_result}'
            )
            return {
                'status': 'error',
                'path': file_path,
                'file_type': file_type,
                'error': 'Failed to read file.',
                'hint': 'Check if the file exists.'
            }
        else:
            content = text_result['content']

    elif file_type == 'media':
        media_result = await read_media_file(file_path, filesystem_client)
        
        if not media_result['ok']:
            logger.error(
                'Media file read failed',
                f'path={file_path} result={media_result}'
            )
            return {
                'status': 'error',
                'path': file_path,
                'file_type': file_type,
                'error': 'Failed to read file.',
                'hint': 'Check if the file exists.'
            }
        else:
            media_content = media_result['content'][0]
            ocr_text = await run_document_ocr(
                media_content['data'], 
                media_content['mimeType'], 
                mistral_api_key, 
                mistral_ocr_endpoint, 
                mistral_ocr_model
            )
            content = ocr_text['markdown']

    else:
        logger.error(
            'Incorrect file_type',
            f'The file_type passed by the agent is not supported, file_type: {file_type}'
        )
        return {
            'status': 'error',
            'path': file_path,
            'file_type': file_type,
            'error': 'Incorrect file_type.',
            'hint': 'Choose the correct file_type and rerun the tool.',
        }
    
    logger.success(f'File read successfully: {file_path}')
    return {
        'status': 'success',
        'path': file_path,
        'file_type': file_type,
        'content': content
    }

ManageMode = Literal['write_file', 'create_directory', 'list_directory', 'directory_tree']
async def manage_files(path: str, mode: ManageMode, content: str | None, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    logger.tool('manage_files', {'path': path, 'mode': mode})

    if mode == 'write_file':
        if content is None:
            logger.error(
                'Content is empty',
                f'path={path} content={content}'
            )
            return {
                'status': 'error',
                'path': path,
                'mode': mode,
                'content': content,
                'error': 'Content is empty.',
                'hint': 'Provide the content to be saved to the file.',
            }
        result = await write_file(file_path=path, content=content, filesystem_client=filesystem_client)

    elif mode == 'create_directory':
        result = await create_directory(dir_path=path, filesystem_client=filesystem_client)

    elif mode == 'list_directory':
        result = await list_directory(dir_path=path, filesystem_client=filesystem_client)

    elif mode == 'directory_tree':
        result = await directory_tree(dir_path=path, filesystem_client=filesystem_client)

    else:
        logger.error(
            'Incorrect mode',
            f'The mode passed by the agent is not supported, mode: {mode}'
        )
        return {
            'status': 'error',
            'path': path,
            'mode': mode,
            'error': 'Incorrect mode.',
            'hint': 'Choose the correct mode and rerun the tool.',
        }

    if not result['ok']:
        logger.error(
            'Manage file failed',
            f'path={path} result={result} mode={mode}'
        )
        return {
            'status': 'error',
            'path': path,
            'mode': mode,
            'error': 'Failed to manage file.'
        }

    return {
        'status': 'success',
        'path': path,
        'mode': mode,
        'content': result['content']
    }

async def send_declaration(task_name: str, declaration_path: str, hub_client: AiDevsHubClient, filesystem_client: MCPFileSystemClient) -> dict[str, Any]:
    logger.tool('send_declaration', {'task_name': task_name, 'declaration_path': declaration_path})
    declaration = await read_text_file(declaration_path, filesystem_client)
    if not declaration['ok']:
        logger.error(
            'Declaration file read failed',
            f'path={declaration_path} result={declaration}'
        )

    result = await send_answer(task_name, declaration['content'], hub_client)
    return result