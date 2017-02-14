import jsonschema
import logging

from utils.module_import import get_class


def get_rules_provider_class(rp_id: str):
    return get_class('rules provider', rp_id)


def validate_rules_set(rules_set: dict):
    schema = {
        'title': 'Rules set',
        'type': 'object',
        'properties': {
            'policy': {
                'title': 'Rules set\'s policy',
                'type': 'string',
                'enum': ['skip', 'warning', 'error']
            },
            'patterns': {
                'title': 'Rules set\'s patterns',
                'type': 'array',
                'items': {
                    'title': 'Rules set\'s pattern',
                    'type': 'array',
                    'items': [
                        {
                            'title': 'Pattern\'s regular expression',
                            'type': 'string'
                        },
                        {
                            'title': 'Pattern\'s options',
                            'type': 'object',
                            'properties': {
                                'passthrough': {
                                    'type': 'boolean'
                                }
                            },
                            'additionalProperties': False
                        },
                        {
                            'title': 'Pattern\'s action name',
                            'type': 'string'
                        },
                        {
                            'title': 'Pattern\'s action parameters',
                            'type': 'object'
                        }
                    ],
                    'minItems': 3,
                    'additionalItems': False
                },
                'minItems': 1
            }
        },
        'required': ['policy', 'patterns', ]
    }
    logging.debug('Validating rules set...')
    jsonschema.validate(rules_set, schema)
