tools = [
    {
        'type': 'function',
        'name': 'check_package_status',
        'description': 'Check the status of the package and return the details.',
        'parameters': {
            'type': 'object',
            'properties': {
                'packageid': {
                    'type': 'string',
                    'description': 'The package id provided by the operator.'
                }
            },
            'required': [
                'packageid'
            ],
            'additionalProperties': False
        },
        'strict': False
    },
    {
        'type': 'function',
        'name': 'redirect_package',
        'description': 'Redirect the package to another destination and return the confirmation code',
        'parameters': {
            'type': 'object',
            'properties': {
                'packageid': {
                    'type': 'string',
                    'description': 'The package id provided by the operator.'
                },
                'destination': {
                    'type': 'string',
                    'description': 'The destination where the package should be delivered.'
                },
                'code': {
                    'type': 'string',
                    'description': 'The security code provided by the operator.'
                }
            },
            'required': [
                'packageid',
                'destination',
                'code'
            ],
            'additionalProperties': False
        },
        'strict': True
    }
]