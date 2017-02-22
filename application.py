import logging
import sys
import json
import os

from datetime import datetime
from traceback import TracebackException

import commands


class ConfigurationException(Exception):
    pass


class Application:

    def __init__(self, base_dir, args, conf=None):
        self._args = args
        self._conf = conf
        self._base_dir = base_dir

        os.chdir(base_dir)
        self._configure_logger()

    @property
    def args(self):
        return self._args

    @property
    def conf(self) -> dict:
        if not self._conf:
            try:
                self._conf = self._validate_configuration(self._get_configuration())
            except ConfigurationException as e:
                sys.stderr.write(str(e))
                sys.exit(1)
        return self._conf

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def exec(self):
        command = getattr(commands, 'command_{}'.format(self.args.command))
        try:
            command()
        except Exception as e:
            tbe = TracebackException.from_exception(e)
            logging.critical(' '.join(list(tbe.format())))
            sys.exit(1)
        logging.info('All done - terminating')

    def _get_configuration(self) -> dict:
        try:
            with open(self.args.conf_path) as c_file:
                return json.load(c_file)
        except FileNotFoundError:
            sys.stderr.write('Configuration file not found: "{}".'.format(self.args.conf_path))
            sys.exit(1)
        except ValueError as e:
            sys.stderr.write('Configuration file "{}" is not a valid JSON document: {}'.format(
                self.args.conf_path, str(e)))
            sys.exit(1)

    @staticmethod
    def _validate_configuration(raw_conf: dict) -> dict:

        def _required(pl: list) -> None:
            for p in pl:
                if p not in raw_conf:
                    raise ConfigurationException('Required configuration parameter "{}" is missing.'.format(p))

        def _is_a_file(pl: list) -> None:
            for p in pl:
                raw_conf[p] = os.path.abspath(raw_conf[p])
                if not os.path.isfile(raw_conf[p]):
                    raise ConfigurationException(
                        'Path in configuration parameter {} "{}" is not a file.'.format(p, raw_conf[p])
                    )

        def _is_a_dir(pl: list) -> None:
            for p in pl:
                raw_conf[p] = os.path.abspath(raw_conf[p])
                if not os.path.isdir(raw_conf[p]):
                    raise ConfigurationException(
                        'Path in configuration parameter {} "{}" is not a directory.'.format(p, raw_conf[p])
                    )

        params = ['ffmpeg_path', 'ffprobe_path', 'temp_dir', 'out_dir', 'log_dir', ]

        _required(params)
        _is_a_file(['ffmpeg_path', 'ffprobe_path', ])
        _is_a_dir(['temp_dir', 'out_dir', 'log_dir', ])

        return dict([(k, raw_conf[k]) for k in params])

    def _configure_logger(self) -> None:
        log_dir = self.conf['log_dir']
        log_split = self.args.log_split
        log_level = self.args.log_level
        verbosity = self.args.verbosity
        if log_split:
            log_file = os.path.join(log_dir, 'autoarchive-{}.log'.format(datetime.today().strftime('%Y%m%d%H%M%S')))
            file_mode = 'w'
        else:
            log_file = os.path.join(log_dir, 'autoarchive.log')
            file_mode = 'a'

        logger = logging.getLogger('')
        logger.setLevel(logging.NOTSET)

        file = logging.FileHandler(log_file, file_mode)
        file.setLevel(getattr(logging, log_level))
        file.setFormatter(
            logging.Formatter('%(process)-6d %(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(file)

        if verbosity != 'NONE':
            console = logging.StreamHandler()
            console.setLevel(getattr(logging, verbosity))
            console.setFormatter(logging.Formatter('%(relativeCreated)-10d %(module)-18s %(levelname)s: %(message)s'))
            logger.addHandler(console)

        logging.debug('Logger initiated')
