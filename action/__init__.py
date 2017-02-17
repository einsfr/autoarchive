import os
import logging

from utils.module_import import get_class
from args import get_args


def get_action_class(action_id: str):
    return get_class('action', action_id)


class AbstractAction:

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        raise NotImplementedError


class OutDirCreatingAction(AbstractAction):

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        simulate = get_args().simulate
        if not simulate:
            logging.debug('Creating output directory "{}"...'.format(out_dir_path))
            if not simulate:
                os.makedirs(out_dir_path, exist_ok=True)

