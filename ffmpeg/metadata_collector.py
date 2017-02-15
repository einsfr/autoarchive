import logging

from utils.cache import HashCacheMixin, CacheMissException
from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver


class FFprobeMetadataResult:

    def __init__(self, info: dict):
        self._info = info

    @property
    def v_streams(self) -> dict:
        pass

    @property
    def vs_count(self) -> int:
        pass

    @property
    def a_streams(self) -> dict:
        pass

    @property
    def as_count(self) -> int:
        pass

    @property
    def format(self) -> dict:
        pass

    def get_field_mode(self, stream_selector) -> int:
        pass


class FFprobeMetadataCollector(HashCacheMixin):

    def __init__(self, conf: dict, timeout: int=5):
        super().__init__(cache_size=10)
        self._conf = conf
        self._timeout = timeout
        logging.debug('Creating FFprobeInfoCommand object...')
        self._ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        logging.debug('Creating FFprobeInterlacedProgressiveSolver object...')
        self._int_prog_solver = FFprobeInterlacedProgressiveSolver(self._conf)

    def get_metadata(self, input_url: str) -> FFprobeMetadataResult:
        try:
            cached_value = self._from_cache(input_url)
        except CacheMissException:
            pass
        else:
            return cached_value
        logging.debug('Trying to get file metadata from ffprobe...')
        result = FFprobeMetadataResult(self._ffprobe_info.exec(input_url, show_programs=False))
        self._to_cache(input_url, result)
        return result
