import logging

from action import AbstractAction


class SkipAction(AbstractAction):

    def run(self, input_url: str, action_params: dict, out_dir_path: str):
        logging.debug('Skipping file "{}"...'.format(input_url))
