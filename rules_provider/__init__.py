import importlib
import logging


def get_rules_provider(rp_id: str):
    module_name = 'rules_provider.{}'.format(rp_id.lower())
    logging.info('Importing rules provider module {}...'.format(module_name))
    module = importlib.import_module(module_name)
    class_name = '{}RulesProvider'.format(rp_id.capitalize())
    logging.info('Trying to get rules provider class {}...'.format(class_name))
    return getattr(module, class_name)()


def validate_rules_set(rules_set: dict):
    pass
