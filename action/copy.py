""" Модуль с классом `CopyAction`

"""

import logging
import os
import shutil

from action import OutDirCreatingAction


class CopyAction(OutDirCreatingAction):
    """ Действие, в котором входной файл копируется в выходную папку

    """

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool) -> None:
        super().run(input_url, action_params, out_dir_path, simulate)
        out_path = os.path.join(out_dir_path, os.path.split(input_url)[1])
        logging.info('Copying file from "{}" to "{}"...'.format(input_url, out_path))
        if not simulate:
            shutil.copy(input_url, out_path)
        logging.info('Done')
