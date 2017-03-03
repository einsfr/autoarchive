import logging
import sys
import json
import os

from datetime import datetime
from traceback import TracebackException

from rules_provider import get_rules_provider_class
from dispatcher import get_dispatcher_class
from converter import get_converter_class

VERSION = '0.2'


class ConfigurationException(Exception):
    pass


class Application:

    def __init__(self, base_dir, args, conf=None):
        self._args = args
        self._conf = None
        self._conf_override = conf
        self._base_dir = base_dir

        os.chdir(base_dir)
        self._configure_logger()

    @property
    def args(self):
        return self._args

    @property
    def conf(self) -> dict:
        if not self._conf:
            self._conf = self._validate_configuration(
                self._get_configuration() if self._conf_override is None else self._conf_override
            )
        return self._conf

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def exec(self):
        command = getattr(self, '_command_{}'.format(self.args.command))
        logging.info('Starting "{}" command...'.format(self.args.command))
        try:
            command()
        except Exception as e:
            tbe = TracebackException.from_exception(e)
            logging.critical(' '.join(list(tbe.format())))
            raise e
        logging.info('All done - terminating')

    def _get_configuration(self) -> dict:
        with open(self.args.conf_path) as c_file:
            return json.load(c_file)

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

    def _command_run(self):
        rules_provider = get_rules_provider_class(self.args.rules_provider)()
        rules_set = rules_provider.get_rules(self.args.rules_set)
        if not rules_set:
            raise ValueError('Rules set can\'t be empty')
        if type(rules_set) != dict:
            raise TypeError('Rules set must be a dictionary')
        logging.debug('Rules set ready')
        logging.debug('Starting dispatcher...')
        get_dispatcher_class(self.args.dispatcher)(
            self.args.input_url, rules_set, self.conf['out_dir'], self.args.dir_depth, self.args.use_in_dir_as_root,
            self.args.simulate
        ).dispatch()

    def _command_version(self):
        sys.stdout.write(VERSION)

    def _command_convert(self):
        logging.debug('Starting converter...')
        get_converter_class(self.args.converter)(
            self.args.input_url, self.args.profile, self.conf['out_dir'], self.args.use_in_dir_as_root,
            self.args.simulate
        ).convert()
