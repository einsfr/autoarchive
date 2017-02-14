import os
import logging
import subprocess
import json
import hashlib
from collections import OrderedDict

from ffmpeg.exceptions import FFprobeTerminatedException, FFprobeProcessException, FFprobeBinaryNotFound


class FFprobeBaseCommand:

    DEFAULT_ARGS = ['-hide_banner', '-of', 'json']
    CACHE_SIZE = 10

    def __init__(self, bin_path: str, timeout: int=5):
        bin_path = os.path.abspath(bin_path)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            msg = 'FFprobe binary not found: "{}"'.format(bin_path)
            logging.critical(msg)
            raise FFprobeBinaryNotFound(msg)
        self._bin_path = bin_path
        self._timeout = timeout
        self._cache = OrderedDict()

    def _to_cache(self, hash_id: str, item):
        self._cache[hash_id] = item
        if len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)

    def _from_cache(self, hash_id: str):
        return self._cache[hash_id]

    def _exec(self, args: list) -> dict:
        exec_hash = hashlib.sha1(''.join(args).encode()).hexdigest()
        try:
            cached_value = self._from_cache(exec_hash)
        except KeyError:
            logging.debug('FFprobe cache miss')
            pass
        else:
            logging.debug('FFprobe cache hit')
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
                self._to_cache(exec_hash, result)
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
