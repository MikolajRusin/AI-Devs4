tools = [
    {
        'type': 'function',
        'function': {
            'name': 'download_people_data',
            'description': 'Download the people CSV file from the hub and return the local file path. Use this when you need the source dataset path.',
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': [],
                'additionalProperties': False,
            },
            'strict': True,
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'filter_people',
            'description': 'Read a people CSV file from people_data_path, filter rows by gender, city, and age range, save the result to filtered_people.csv, and return the new file path.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'people_data_path': {
                        'type': 'string',
                        'description': 'Local path to the source people CSV file.'
                    },
                    'gender': {
                        'type': 'string',
                        'description': "Gender value to filter by, for example 'M' or 'F'."
                    },
                    'city': {
                        'type': 'string',
                        'description': 'Birth city value to filter by.'
                    },
                    'lower_age_bound': {
                        'type': 'integer',
                        'description': 'Minimum age, inclusive.'
                    },
                    'upper_age_bound': {
                        'type': 'integer',
                        'description': 'Maximum age, inclusive.'
                    }
                },
                'required': [
                    'people_data_path',
                    'gender',
                    'city',
                    'lower_age_bound',
                    'upper_age_bound',
                ],
                'additionalProperties': False,
            },
            'strict': True,
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'tag_jobs',
            'description': 'Read filtered_people_path, extract unique job descriptions, tag them with job categories, update the CSV with job_id values, save tagged_jobs.json, and return both output paths.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filtered_people_path': {
                        'type': 'string',
                        'description': 'Local path to the filtered people CSV file.'
                    }
                },
                'required': [
                    'filtered_people_path',
                ],
                'additionalProperties': False,
            },
            'strict': True,
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_job_tags',
            'description': 'Return available job tags with their IDs and names. Use this tool when you need to identify the correct tag_id.',
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': [],
                'additionalProperties': False,
            },
            'strict': True,
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'filter_people_by_job_tag_id',
            'description': 'Read filtered_people_path and tagged_jobs_path, keep only people whose job_id has the requested tag_id.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filtered_people_path': {
                        'type': 'string',
                        'description': 'Local path to filtered_people.csv containing people data with job_id column.'
                    },
                    'tagged_jobs_path': {
                        'type': 'string',
                        'description': 'Local path to tagged_jobs.json containing the mapping from job_id to tag IDs.'
                    },
                    'tag_id': {
                        'type': 'integer',
                        'description': 'The selected job tag ID used to filter people.'
                    }
                },
                'required': [
                    'filtered_people_path',
                    'tagged_jobs_path',
                    'tag_id'
                ],
                'additionalProperties': False,
            },
            'strict': True,
        },
    }
]
