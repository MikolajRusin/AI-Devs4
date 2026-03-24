TOOLS_DEFINITION = [
    {
        'type': 'function',
        'name': 'load_board',
        'description': (
            'Download and analyze a full 3x3 board image. '
            'Use this to get the exits for all 9 board cells at once.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'board_type': {
                    'type': 'string',
                    'description': 'Which board image should be analyzed.',
                    'enum': ['current', 'solved']
                }
            },
            'required': ['board_type'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'load_one_tile',
        'description': (
            'Download and analyze a single board tile. '
            'Use this when the state of one specific cell is uncertain and needs closer inspection.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'board_type': {
                    'type': 'string',
                    'description': 'Which board image should be analyzed.',
                    'enum': ['current', 'solved']
                },
                'row': {
                    'type': 'integer',
                    'description': 'Board row number counted from top to bottom.',
                    'minimum': 1,
                    'maximum': 3
                },
                'column': {
                    'type': 'integer',
                    'description': 'Board column number counted from left to right.',
                    'minimum': 1,
                    'maximum': 3
                }
            },
            'required': ['board_type', 'row', 'column'],
            'additionalProperties': False
        }
    },
    {
        'type': 'function',
        'name': 'rotate_one_tile',
        'description': (
            'Rotate a single board tile 90 degrees clockwise on the live board.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'row': {
                    'type': 'integer',
                    'description': 'Board row number counted from top to bottom.',
                    'minimum': 1,
                    'maximum': 3
                },
                'column': {
                    'type': 'integer',
                    'description': 'Board column number counted from left to right.',
                    'minimum': 1,
                    'maximum': 3
                }
            },
            'required': ['row', 'column'],
            'additionalProperties': False
        }
    }
]
