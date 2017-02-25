""" Модуль с классом `SkipAction`

"""

import logging

from action import AbstractAction


class SkipAction(AbstractAction):
    """ Действие, в котором с входным файлом не происходит совсем ничего

    """

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool):
        logging.debug('Skipping file "{}"...'.format(input_url))
