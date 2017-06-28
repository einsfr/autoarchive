""" Модуль с классом `FfmpegConvertAction`

"""

import logging
import os

from dispatcher import ActionRunException
from action import OutDirCreatingAction
from pyffwrapper.ffmpeg import FFmpegBaseCommand
from pyffwrapper import exceptions as ffmpeg_exceptions
from pyffwrapper.metadata_collector import FFprobeMetadataCollector
from pyffwrapper import factory, profile_loader


class FfmpegConvertAction(OutDirCreatingAction):
    """ Действие, в котором используется ffmpeg для выполнения преобразования входного файла

    """

    def __init__(self):
        super().__init__()
        logging.debug('Fetching FFmpegConvertCommand object...')
        self._ffmpeg_convert = factory.ffmpeg_factory.get_ffmpeg_command(FFmpegBaseCommand)
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ffprobe_meta_collector = factory.ffprobe_factory.get_ffprobe_metadata_collector(FFprobeMetadataCollector)

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool) -> None:
        super().run(input_url, action_params, out_dir_path, simulate)
        input_metadata = self._ffprobe_meta_collector.get_metadata(input_url)
        logging.debug('Input metadata: {}'.format(input_metadata))
        context = {
            'input': input_metadata,
            'vars': action_params['profile_vars'] if 'profile_vars' in action_params else {}
        }
        logging.debug('Profile rendering context: \r\n{}'.format(context))
        profile = profile_loader.profile_loader.get_profile(action_params['profile'], context=context)
        logging.debug('Starting FFmpeg conversion...')
        try:
            self._ffmpeg_convert.exec(
                [(profile.inputs[0]['parameters'], input_url)],
                [(o['parameters'], os.path.join(out_dir_path, o['filename'])) for o in profile.outputs],
                simulate
            )
        except (ffmpeg_exceptions.FFmpegInputNotFoundException, ffmpeg_exceptions.FFmpegOutputAlreadyExistsException,
                ffmpeg_exceptions.FFmpegProcessException) as e:
            raise ActionRunException from e
