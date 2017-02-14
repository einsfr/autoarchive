import os
import logging
import subprocess
import json

from ffmpeg.exceptions import FFprobeTerminatedException, FFprobeProcessException, FFprobeBinaryNotFound
from utils.cache import HashCacheMixin, CacheMissException


class FFprobeBaseCommand(HashCacheMixin):

    DEFAULT_ARGS = ['-hide_banner', '-of', 'json']

    def __init__(self, bin_path: str, timeout: int=5):
        super().__init__(cache_size=10)
        bin_path = os.path.abspath(bin_path)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            msg = 'FFprobe binary not found: "{}"'.format(bin_path)
            logging.critical(msg)
            raise FFprobeBinaryNotFound(msg)
        self._bin_path = bin_path
        self._timeout = timeout

    def _exec(self, args: list) -> dict:
        cache_id = ''.join(args)
        try:
            cached_value = self.from_cache(cache_id)
        except CacheMissException:
            pass
        else:
            return cached_value
        logging.debug('Starting {}'.format(' '.join(args)))
        try:
            proc = subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=self._timeout, universal_newlines=True
            )
        except subprocess.TimeoutExpired as e:
            logging.error('FFprobe timeout - terminating')
            raise FFprobeProcessException from e
        if proc.returncode == 0:
            logging.debug('FFprobe done')
            try:
                result = json.loads(proc.stdout)
                self.to_cache(cache_id, result)
                return result
            except ValueError as e:
                logging.error('FFprobe\'s stdout decoding error: {}'.format(str(e)))
                logging.debug('Dumping stdout: {}'.format(proc.stdout))
                raise FFprobeProcessException from e
        elif proc.returncode < 0:
            msg = 'FFprobe terminated with signal {}'.format(abs(proc.returncode))
            raise FFprobeTerminatedException(msg)
        else:
            logging.error('Ffprobe exited with code {}'.format(proc.returncode))
            logging.debug('Dumping stderr: {}'.format(proc.stderr))
            raise FFprobeProcessException()


class FFprobeFrameCommand(FFprobeBaseCommand):

    DEFAULT_ARGS = FFprobeBaseCommand.DEFAULT_ARGS + ['-show_frames']

    def exec(self, in_url: str, select_streams: str=None, read_intervals: str=None) -> dict:
        logging.debug('Building FFprobe command...')
        args = [self._bin_path] + self.__class__.DEFAULT_ARGS
        if select_streams is not None:
            args.append('-select_streams')
            args.append(select_streams)
        if read_intervals is not None:
            args.append('-read_intervals')
            args.append(read_intervals)
        args.append(in_url)

        return self._exec(args)


class FFprobeInfoCommand(FFprobeBaseCommand):

    def exec(self, in_url: str, show_format: bool=True, show_streams: bool=True, show_programs: bool=True) -> dict:
        logging.debug('Building FFprobe command...')
        args = [self._bin_path] + self.__class__.DEFAULT_ARGS
        logging.debug('Appending -show* arguments...')
        if show_format:
            args.append('-show_format')
        if show_streams:
            args.append('-show_streams')
        if show_programs:
            args.append('-show_programs')
        args.append(in_url)

        return self._exec(args)
