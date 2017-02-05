import os
import logging
import uuid
import shutil
import subprocess

from collections import deque
from datetime import datetime

from ffmpeg.exceptions import FFmpegProcessException, FFmpegBinaryNotFound


TRADEMARK_NOTE = 'FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.'


class FFmpegBaseCommand:

    DEFAULT_GENERAL_ARGS = ['-hide_banner', '-n', '-nostdin', '-loglevel', 'warning', '-stats']

    def __init__(self, bin_path: str, tmp_dir: str):
        bin_path = os.path.abspath(bin_path)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            msg = 'FFmpeg binary not found: "{}"'.format(bin_path)
            logging.critical(msg)
            raise FFmpegBinaryNotFound(msg)
        self._bin_path = bin_path
        self._tmp_dir = os.path.abspath(tmp_dir)

    def exec(self, *args, **kwargs):
        logging.info(TRADEMARK_NOTE)


class FFmpegConvert(FFmpegBaseCommand):

    @staticmethod
    def _success_callback(output_mapping: list, simulate: bool) -> None:
        if not simulate:
            logging.info('Moving file from temporary directory...')
            for tmp_path, out_path in output_mapping:
                logging.debug('Temporary file: "{}"; output file: "{}"'.format(tmp_path, out_path))
                if os.path.exists(out_path):
                    logging.warning('Output file "{}" already exists'.format(out_path))
                    head, tail = os.path.split(out_path)
                    name, ext = os.path.splitext(tail)
                    out_path = os.path.join(
                        head,
                        '{}.{}.{}'.format(
                            name,
                            os.path.split(tmp_path)[1],
                            ext
                        )
                    )
                    logging.warning('New output file name: "{}"'.format(out_path))
                shutil.move(tmp_path, out_path)
        logging.info('Done!')

    @staticmethod
    def _progress_callback(frame: int) -> None:
        logging.debug('Processed {} frames'.format(frame))

    @staticmethod
    def _error_callback(return_code: int, proc_log: deque, proc_exception: Exception, tmp_paths: list) -> None:
        logging.info('Removing temporary files...')
        for t in tmp_paths:
            if os.path.exists(t):
                logging.debug('Found: "{}" - removing...')
                os.remove(t)
        raise FFmpegProcessException(
            'Exit code {}.\r\nLast output:\r\n{}\r\nRaised exception: {}'.format(
                return_code, '\r\n'.join(proc_log), proc_exception
            )
        )

    def exec(self, inputs: list, outputs: list, general_args: list=None, simulate: bool=False) -> None:
        super().exec()
        if general_args is None:
            general_args = self.__class__.DEFAULT_GENERAL_ARGS
        logging.info('Building FFmpeg command...')
        args = [self._bin_path]
        logging.debug('General args: {}'.format(general_args))
        args.extend(general_args)

        logging.info('Appending inputs...')
        for i in inputs:
            in_args, in_url = i
            if not os.path.isfile(in_url):
                msg = 'Input file not found: "{}"'.format(in_url)
                logging.error(msg)
                raise FileNotFoundError(msg)
            in_args.append('i')
            in_args.append(in_url)
            logging.debug('Extending args with {}'.format(in_args))
            args.extend(in_args)

        logging.info('Appending outputs...')
        output_mapping = []
        for o in outputs:
            out_args, out_path = o
            if os.path.exists(out_path):
                msg = 'Output file "{}" already exists'.format(out_path)
                logging.error(msg)
                raise FileExistsError(msg)
            tmp_path = os.path.join(self._tmp_dir, uuid.uuid4())
            output_mapping.append((out_path, tmp_path))
            out_args.append(tmp_path)
            logging.debug('Extending args with {}'.format(out_args))
            args.extend(out_args)
        logging.debug('Output mapping: {}'.format(output_mapping))

        logging.info('Starting {}'.format(' '.join(args)))
        if simulate:
            self._success_callback(output_mapping, True)
            return

        proc_log = deque(maxlen=5)
        proc_exception = None
        proc = subprocess.Popen(args, stderr=subprocess.PIPE, universal_newlines=True)
        proc_start_time = datetime.now()
        logging.info('FFmpeg process started at {}'.format(proc_start_time))

        ignoring_progress = False
        try:
            for line in proc.stderr:
                proc_log.append(line)
                if not ignoring_progress and line.startswith('frame='):
                    p = line.find('fps=')
                    try:
                        frame = int(line[6:p].strip())
                    except ValueError:
                        logging.warning(line)
                        logging.warning('Unable to determine conversion progress - ignoring it')
                        ignoring_progress = True
                    else:
                        self._progress_callback(frame)
        except FFmpegProcessException as e:
            proc.terminate()
            proc_exception = e
        except Exception as e:
            proc.terminate()
            logging.error(str(e))
        finally:
            proc.wait()
            proc_end_time = datetime.now()
            logging.info('FFmpeg process finished at {}. Elapsed time: {}'.format(
                proc_end_time, proc_end_time - proc_start_time)
            )
            return_code = proc.returncode
            if return_code != 0:
                self._error_callback(
                    return_code, proc_log, proc_exception,
                    [t for t, o in output_mapping]
                )
            else:
                self._success_callback(output_mapping, False)
