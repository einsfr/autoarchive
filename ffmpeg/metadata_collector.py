import logging

from utils.cache import HashCacheMixin, CacheMissException
from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver


class FFprobeMetadataCollector(HashCacheMixin):

    def __init__(self, conf: dict, timeout: int=5):
        super().__init__(cache_size=10)
        self._conf = conf
        self._timeout = timeout
        logging.debug('Creating FFprobeInfoCommand object...')
        self._ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        logging.debug('Creating FFprobeInterlacedProgressiveSolver object...')
        self._int_prog_solver = FFprobeInterlacedProgressiveSolver(self._conf)

    def get_metadata(self, input_url: str) -> dict:
        try:
            cached_value = self.from_cache(input_url)
        except CacheMissException:
            pass
        else:
            return cached_value
