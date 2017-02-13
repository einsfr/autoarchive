import os
import logging

from utils.module_import import get_class


def get_action_class(action_id: str):
    return get_class('action', action_id)


class AbstractAction:

    def __init__(self, conf: dict, simulate: bool):
        self._conf = conf
        self._simulate = simulate

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        raise NotImplementedError


class OutDirCreatingAction(AbstractAction):

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        if not self._simulate:
            logging.debug('Creating output directory "{}"...'.format(out_dir_path))
            if not self._simulate:
                os.makedirs(out_dir_path, exist_ok=True)

