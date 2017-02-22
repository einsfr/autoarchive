import logging
import os
import json

from dispatcher import ActionRunException
from action import OutDirCreatingAction
from ffmpeg.ffmpeg import FFmpegBaseCommand
from ffmpeg import exceptions as ffmpeg_exceptions
from ffmpeg.metadata_collector import FFprobeMetadataCollector
from ffmpeg import get_ffmpeg_factory


class FfmpegConvertAction(OutDirCreatingAction):

    def __init__(self):
        super().__init__()
        _factory = get_ffmpeg_factory()
        logging.debug('Fetching FFmpegConvertCommand object...')
        self._ffmpeg_convert = _factory.get_ffmpeg_command(FFmpegBaseCommand)
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ffprobe_meta_collector = _factory.get_ffprobe_metadata_collector(FFprobeMetadataCollector)

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        super().run(input_url, action_params, out_dir_path)
        profile_template_name = action_params['profile']


        context = {
            'input': self._ffprobe_meta_collector.get_metadata(input_url)
        }


        logging.debug('Profile rendering complete - loading...')
        try:
            profile_dict = json.loads(profile_data)
        except ValueError as e:
            raise ValueError('Profile {} is not a valid JSON document: {}'.format(profile_template_name, str(e)))
        self._validate_profile(profile_dict)
        logging.debug('Starting FFmpeg conversion...')
        try:
            self._ffmpeg_convert.exec(
                [(profile_dict['inputs'][0]['parameters'], input_url)],
                [(o['parameters'], os.path.join(out_dir_path, o['filename'])) for o in profile_dict['outputs']]
            )
        except (ffmpeg_exceptions.FFmpegInputNotFoundException, ffmpeg_exceptions.FFmpegOutputAlreadyExistsException,
                ffmpeg_exceptions.FFmpegProcessException) as e:
            raise ActionRunException from e
