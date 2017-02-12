import logging
import os
import shutil

from action import AbstractAction


class CopyAction(AbstractAction):

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        out_path = os.path.join(out_dir_path, os.path.split(input_url)[1])
        logging.info('Copying file from "{}" to "{}"...'.format(input_url, out_path))
        if not self._simulate:
            shutil.copy(input_url, out_path)
        logging.info('Done')
