import logging


class FFmpegFactory:

    def __init__(self, ffmpeg_path: str, ffprobe_path: str, temp_dir: str, probe_timeout: int = 5):
        self._ffmpeg_path = ffmpeg_path
        self._temp_dir = temp_dir
        self._ffprobe_path = ffprobe_path
        self._probe_timeout = probe_timeout

        self._objects = {}

    def _get_object(self, cmd_class, *args, **kwargs):
        cmd_class_str = str(cmd_class)
        if cmd_class_str not in self._objects:
            logging.debug('Object of {} not found - creating...'.format(cmd_class_str))
            self._objects[cmd_class_str] = cmd_class(*args, **kwargs)
        return self._objects[cmd_class_str]

    @property
    def objects(self):
        return self._objects

    def get_ffmpeg_command(self, cmd_class, simulate: bool = False):
        return self._get_object(cmd_class, self._ffmpeg_path, self._temp_dir, simulate)

    def get_ffprobe_command(self, cmd_class):
        return self._get_object(cmd_class, self._ffprobe_path, self._probe_timeout)

    def get_ffprobe_field_mode_solver(self, cmd_class):
        return self._get_object(cmd_class)

    def get_ffprobe_metadata_collector(self, cmd_class):
        return self._get_object(cmd_class)

    def get_ffprobe_metadata_filter(self, cmd_class):
        return self._get_object(cmd_class)
