TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'fetch_logs',
        'description': 'Fetch the latest failure logs from the hub and save them locally.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    },
    {
        'type': 'function',
        'name': 'search_logs',
        'description': 'Search and filter logs by severity level, keywords, duplicate grouping, and result limit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the log file.'
                },
                'event': {
                    'type': 'array',
                    'description': 'List of log severity levels to include.',
                    'items': {
                        'type': 'string',
                        'enum': ['INFO', 'WARN', 'ERRO', 'CRIT']
                    }
                },
                'search': {
                    'type': 'array',
                    'description': 'List of keywords or phrases to search for in log messages.',
                    'items': {
                        'type': 'string'
                    }
                },
                'first_n_per_group': {
                    'type': 'integer',
                    'description': 'Maximum number of logs to keep for each duplicate group. Recommended value: 1.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of logs to return. Maximum allowed value: 50. A 50-log response is expected behavior for one iteration, not an error. If more evidence is needed, run another narrower search instead of trying to force a larger batch.'
                }
            },
            'required': ['path']
        }
    },
    {
        'type': 'function',
        'name': 'read_file',
        'description': 'Read the content of a text file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the file.'
                }
            },
            'required': ['path']
        }
    },
    {
        'type': 'function',
        'name': 'manage_files',
        'description': 'Write files, create directories, list directory contents, or view directory tree. Use mode="write_file" when you need to persist your findings to disk.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Target file or directory path.'
                },
                'mode': {
                    'type': 'string',
                    'enum': ['write_file', 'create_directory', 'list_directory', 'directory_tree'],
                    'description': 'Operation mode.'
                },
                'content': {
                    'type': 'string',
                    'description': 'File content to save when mode is write_file. Required when writing a result file.'
                }
            },
            'required': ['path', 'mode']
        }
    },
    {
        'type': 'function',
        'name': 'count_tokens',
        'description': 'Count the number of tokens in a log file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'logs_path': {
                    'type': 'string',
                    'description': 'Path to the file containing logs.'
                }
            },
            'required': ['logs_path']
        }
    },
    {
        'type': 'function',
        'name': 'send_logs',
        'description': 'Read condensed logs from a file and send them to the hub for verification.',
        'parameters': {
            'type': 'object',
            'properties': {
                'logs_path': {
                    'type': 'string',
                    'description': 'Path to the file containing the final condensed logs that should be sent to the hub.'
                }
            },
            'required': ['logs_path']
        }
    },
    {
        'type': 'function',
        'name': 'delegate_to_agent',
        'description': 'Delegate a task to a specialized subagent.',
        'parameters': {
            'type': 'object',
            'properties': {
                'agent_name': {
                    'type': 'string',
                    'description': 'Name of the subagent.',
                    'enum': ['log_search_agent']
                },
                'task': {
                    'type': 'string',
                    'description': 'Task for the subagent.'
                }
            },
            'required': ['agent_name', 'task']
        }
    }
]
