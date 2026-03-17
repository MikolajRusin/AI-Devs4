TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'download_documents',
        'description': (
            'Download one or more documents, save them locally and return the path where the document was saved. '
            'Use this when you know the document file names you want to inspect.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'document_names': {
                    'type': 'array',
                    'description': 'List of document file names to download.',
                    'items': {
                        'type': 'string'
                    },
                    'minItems': 1
                }
            },
            'required': ['document_names'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'read_file',
        'description': (
            'Read a local file. For text files it returns the text content. '
            'For image files it runs OCR and returns extracted markdown text.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'Local path to the file that should be read.'
                },
                'file_type': {
                    'type': 'string',
                    'description': 'Type of file to read.',
                    'enum': ['text', 'media']
                }
            },
            'required': ['file_path', 'file_type'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'manage_files',
        'description': (
            'Manage local files and directories. Use it to write a file, create a directory, '
            'list directory contents, or inspect the full directory tree.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Target local path for the operation.'
                },
                'mode': {
                    'type': 'string',
                    'description': 'Filesystem operation to execute.',
                    'enum': ['write_file', 'create_directory', 'list_directory', 'directory_tree']
                },
                'content': {
                    'type': 'string',
                    'description': 'Text content to write when mode is write_file.'
                }
            },
            'required': ['path', 'mode'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'send_declaration',
        'description': (
            'Send the path of the final prepared declaration to the endpoint for the given task.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'task_name': {
                    'type': 'string',
                    'description': 'Task name to verify, for example sendit.'
                },
                'declaration_path': {
                    'type': 'string',
                    'description': 'Local path to the file containing the final declaration.'
                }
            },
            'required': ['task_name', 'declaration_path'],
            'additionalProperties': False
        }
    }
]
