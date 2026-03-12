tools = [
    {
        'type': 'function',
        'function': {
            'name': 'download_people_data',
            'description': 'Download the source people dataset and return the local CSV path.',
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
            'description': 'Filter the people CSV by gender, city, and age range, save the result, and return the filtered CSV path and row count.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'people_data_path': {
                        'type': 'string',
                        'description': 'Local path to the source people CSV file.'
                    },
                    'gender': {
                        'type': 'string',
                        'description': "Gender to keep, for example 'M' or 'F'."
                    },
                    'city': {
                        'type': 'string',
                        'description': 'City value to keep.'
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
            'description': 'Tag job descriptions from the filtered people CSV, save tagged_jobs.json, and return both output paths.',
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
            'description': 'Return available job tag IDs and names.',
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
            'description': 'Keep only people whose tagged job matches the selected tag ID and return the updated CSV path.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filtered_people_path': {
                        'type': 'string',
                        'description': 'Local path to the filtered people CSV file.'
                    },
                    'tagged_jobs_path': {
                        'type': 'string',
                        'description': 'Local path to tagged_jobs.json.'
                    },
                    'tag_id': {
                        'type': 'integer',
                        'description': 'Job tag ID to keep.'
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
    },
    {
        'type': 'function',
        'function': {
            'name': 'download_power_plant_locations',
            'description': 'Download the power plant dataset, add coordinates for each plant, save the enriched JSON, and return its path.',
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': [],
                'additionalProperties': False,
            },
            'strict': True,
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'identify_power_plant_suspect',
            'description': 'Find the filtered person whose known locations are closest to a power plant and return that person with the matched power plant code.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'power_plant_data_path': {
                        'type': 'string',
                        'description': 'Local path to the power plant JSON file with plant coordinates.'
                    },
                    'filtered_people_path': {
                        'type': 'string',
                        'description': 'Local path to the filtered people CSV file.'
                    }
                },
                'required': [
                    'power_plant_data_path',
                    'filtered_people_path',
                ],
                'additionalProperties': False,
            },
            'strict': True,
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_access_level',
            'description': 'Fetch the access level for the selected suspect.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'First name of the suspect.'
                    },
                    'surname': {
                        'type': 'string',
                        'description': 'Surname of the suspect.'
                    },
                    'birth_year': {
                        'type': 'integer',
                        'description': 'Birth year of the suspect.'
                    }
                },
                'required': [
                    'name',
                    'surname',
                    'birth_year',
                ],
                'additionalProperties': False,
            },
            'strict': True,
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_message',
            'description': 'Send the final suspect report with name, surname, access level, and power plant code to verify the answer.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'First name of the suspect.'
                    },
                    'surname': {
                        'type': 'string',
                        'description': 'Surname of the suspect.'
                    },
                    'access_level': {
                        'type': 'integer',
                        'description': 'Access level of the suspect.'
                    },
                    'power_plant_code': {
                        'type': 'string',
                        'description': 'Matched power plant code in PWR0000PL format.'
                    },
                    'message_header': {
                        'type': 'string',
                        'description': 'Message topic or header.'
                    }
                },
                'required': [
                    'name',
                    'surname',
                    'access_level',
                    'power_plant_code',
                    'message_header',
                ],
                'additionalProperties': False,
            },
            'strict': True,
        },
    }
]
