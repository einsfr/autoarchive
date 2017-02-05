import importlib
import logging


def get_dispatcher(disp_id: str):
    module_name = 'dispatcher.{}'.format(disp_id.lower())
    logging.info('Importing dispatcher module {}...'.format(module_name))
    module = importlib.import_module(module_name)
    class_name = '{}Dispatcher'.format(disp_id.capitalize())
    logging.info('Trying to get dispatcher class {}...'.format(class_name))
    return getattr(module, class_name)()
