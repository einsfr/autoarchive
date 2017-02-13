import logging
import importlib


_module_cache = {}


def get_module(module_type: str, module_id: str):
    module_name = '{}.{}'.format(module_type.replace(' ', '_'), module_id.lower())
    logging.debug('Searching for {} module {}...'.format(module_type, module_name))
    try:
        module = _module_cache[module_name]
        logging.debug('Module cache hit')
    except KeyError:
        logging.debug('Module cache miss - importing {}...'.format(module_name))
        module = importlib.import_module(module_name)
    return module


def get_class(module_type: str, module_id: str):
    module = get_module(module_type, module_id)
    class_name = '{}{}'.format(
        ''.join([v.capitalize() for v in module_id.split('.')]),
        ''.join([v.capitalize() for v in module_type.split(' ')])
    )
    logging.debug('Trying to get {} class {}...'.format(module_type, class_name))
    return getattr(module, class_name)
