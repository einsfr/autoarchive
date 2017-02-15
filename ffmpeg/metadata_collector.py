import logging
import os

from utils.cache import HashCacheMixin, CacheMissException
from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver


class FFprobeMetadataResult:

    def __init__(self, input_url: str, info: dict, int_prog_solver: FFprobeInterlacedProgressiveSolver):
        self._input_url = input_url
        self._info = info
        self._int_prog_solver = int_prog_solver
        self._av_streams_found = False
        self._v_streams_numbers = []
        self._a_streams_numbers = []
        self._field_mode = {}
        self._filename = ''
        self._filename_ext = ''

    def _find_av_streams(self):
        logging.debug('Searching for video and audio streams...')
        for n, s in enumerate(self._info['streams']):
            if s['codec_type'] == 'video':
                self._v_streams_numbers.append(n)
            elif s['codec_type'] == 'audio':
                self._a_streams_numbers.append(n)
        logging.debug('Found {} video stream(s) and {} audio stream(s)'.format(
            len(self._v_streams_numbers), len(self._a_streams_numbers)
        ))

    @property
    def v_streams(self) -> dict:
        if not self._av_streams_found:
            self._find_av_streams()
        return {self._info['streams'][n]['index']: self._info['streams'][n] for n in self._v_streams_numbers}

    @property
    def vs_count(self) -> int:
        if not self._av_streams_found:
            self._find_av_streams()
        return len(self._v_streams_numbers)

    @property
    def a_streams(self) -> dict:
        if not self._av_streams_found:
            self._find_av_streams()
        return {self._info['streams'][n]['index']: self._info['streams'][n] for n in self._a_streams_numbers}

    @property
    def as_count(self) -> int:
        if not self._av_streams_found:
            self._find_av_streams()
        return len(self._a_streams_numbers)

    @property
    def format(self) -> dict:
        return self._info['format']

    @property
    def filename(self) -> str:
        if not self._filename:
            self._filename = os.path.splitext(self.filename_ext)[0]
        return self._filename

    @property
    def filename_ext(self) -> str:
        if not self._filename_ext:
            self._filename_ext = os.path.split(self._input_url)[1]
        return self._filename_ext

    def get_field_mode(self, stream_number: int) -> int:
        if stream_number not in self._field_mode:
            self._field_mode[stream_number] = self._int_prog_solver.solve(self._input_url, stream_number)
        return self._field_mode[stream_number]

    def __str__(self):
        return {
            'a_streams': self.a_streams,
            'as_count': self.as_count,
            'filename': self.filename,
            'filename_ext': self.filename_ext,
            'format': self.format,
            'v_streams': self.v_streams,
            'vs_count': self.vs_count,
        }


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
        result = FFprobeMetadataResult(
            input_url,
            self._ffprobe_info.exec(input_url, show_programs=False),
            self._int_prog_solver
        )
        self._to_cache(input_url, result)
        return result
