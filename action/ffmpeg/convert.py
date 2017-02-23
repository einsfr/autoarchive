import logging
import os

from dispatcher import ActionRunException
from action import OutDirCreatingAction
from ffmpeg.ffmpeg import FFmpegBaseCommand
from ffmpeg import exceptions as ffmpeg_exceptions
from ffmpeg.metadata_collector import FFprobeMetadataCollector
from ffmpeg import factory, profile_loader


class FfmpegConvertAction(OutDirCreatingAction):

    def __init__(self):
        super().__init__()
        logging.debug('Fetching FFmpegConvertCommand object...')
        self._ffmpeg_convert = factory.ffmpeg_factory.get_ffmpeg_command(FFmpegBaseCommand)
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ffprobe_meta_collector = factory.ffprobe_factory.get_ffprobe_metadata_collector(FFprobeMetadataCollector)

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool) -> None:
        super().run(input_url, action_params, out_dir_path, simulate)
        profile = profile_loader.profile_loader.get_profile(action_params['profile'], context={
            'input': self._ffprobe_meta_collector.get_metadata(input_url)
        })
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
