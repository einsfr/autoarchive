import os
import logging
import subprocess
import json

from ffmpeg.exceptions import FFprobeTerminatedException, FFprobeProcessException, FFprobeBinaryNotFound


logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')


class FFprobeBaseCommand:

    DEFAULT_ARGS = ['-hide_banner', '-of', 'json']

    def __init__(self, bin_path: str, timeout: int=5):
        bin_path = os.path.abspath(bin_path)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            msg = 'FFprobe binary not found: "{}"'.format(bin_path)
            logging.critical(msg)
            raise FFprobeBinaryNotFound(msg)
        self._bin_path = bin_path
        self._timeout = timeout

    def _exec(self, args: list) -> dict:
        logging.info('Starting {}'.format(' '.join(args)))
        try:
            proc = subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=self._timeout, universal_newlines=True
            )
        except subprocess.TimeoutExpired as e:
            logging.error('FFprobe timeout - terminating')
            raise FFprobeProcessException from e
        if proc.returncode == 0:
            logging.info('FFprobe done')
            try:
                return json.loads(proc.stdout)
            except ValueError as e:
                logging.error('FFprobe\'s stdout decoding error: {}'.format(str(e)))
                logging.debug('Dumping stdout: {}'.format(proc.stdout))
                raise FFprobeProcessException from e
        elif proc.returncode < 0:
            msg = 'FFprobe terminated with signal {}'.format(abs(proc.returncode))
            logging.info(msg)
            raise FFprobeTerminatedException(msg)
        else:
            logging.error('Ffprobe exited with code {}'.format(proc.returncode))
            logging.debug('Dumping stderr: {}'.format(proc.stderr))
            raise FFprobeProcessException()


class FFprobeFrameCommand(FFprobeBaseCommand):

    DEFAULT_ARGS = FFprobeBaseCommand.DEFAULT_ARGS + ['-show_frames']

    def exec(self, in_url: str, select_streams: str=None, read_intervals: str=None) -> dict:
        logging.info('Building FFprobe command...')
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
        logging.info('Building FFprobe command...')
        args = [self._bin_path] + self.__class__.DEFAULT_ARGS
        logging.info('Appending -show* arguments...')
        if show_format:
            args.append('-show_format')
        if show_streams:
            args.append('-show_streams')
        if show_programs:
            args.append('-show_programs')
        args.append(in_url)

        return self._exec(args)
