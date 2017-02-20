import os
import logging

from jinja2 import Environment, FileSystemLoader

logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')


def _get_ff_profiles_dir():  # may be reimplemented
    from autoarchive import BASE_DIR
    return os.path.join(BASE_DIR, 'ff_profiles')


jinja_env = Environment(
    loader=FileSystemLoader(_get_ff_profiles_dir()),
    autoescape=False
)


class FFmpegFactory:

    def __init__(self, conf: dict, simulate: bool = False, probe_timeout: int = 5):
        self._ffmpeg_path = conf['ffmpeg_path']
        self._temp_dir = conf['temp_dir']
        self._ffprobe_path = conf['ffprobe_path']
        self._simulate = simulate
        self._probe_timeout = probe_timeout
        self._objects = {}

    def _get_object(self, cmd_class, *args, **kwargs):
        cmd_class_str = str(cmd_class)
        if cmd_class_str not in self._objects:
            logging.debug('Object of {} not found - creating...'.format(cmd_class_str))
            self._objects[cmd_class_str] = cmd_class(*args, **kwargs)
        return self._objects[cmd_class_str]

    def get_ffmpeg_command(self, cmd_class):
        return self._get_object(cmd_class, self._ffmpeg_path, self._temp_dir, self._simulate)

    def get_ffprobe_command(self, cmd_class):
        return self._get_object(cmd_class, self._ffprobe_path, self._probe_timeout)

    def get_ffprobe_field_mode_solver(self, cmd_class):
        return self._get_object(cmd_class)

    def get_ffprobe_metadata_collector(self, cmd_class):
        return self._get_object(cmd_class)

    def get_ffprobe_metadata_filter(self, cmd_class):
        return self._get_object(cmd_class)


_factory = None


def get_ffmpeg_factory() -> FFmpegFactory:
    global _factory
    if _factory is None:
        logging.debug('Initializing FFmpegFactory...')
        _factory = _get_ffmpeg_factory()
    return _factory


def _get_ffmpeg_factory():  # may be reimplemented
    from configuration import get_configuration
    from args import get_args

    args = get_args()
    return FFmpegFactory(get_configuration(), args.simulate)
