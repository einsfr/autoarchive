import os
import logging
import sys

from datetime import datetime
from traceback import TracebackException

from args import get_arguments_parser
from configuration import get_configuration


BASE_DIR = os.path.dirname(__file__)
TRACE_LEVEL_NUM = 15


def trace(self, msg, *arg, **kwargs):
    self.log(TRACE_LEVEL_NUM, msg, *arg, **kwargs)


def configure_logger(log_dir: str, log_split: bool, log_level: str, verbosity: str) -> None:
    if log_split:
        log_file = os.path.join(log_dir, '{}.log'.format(datetime.today().strftime('%Y%m%d%H%M%S')))
        file_mode = 'w'
    else:
        log_file = os.path.join(log_dir, 'autoarchive.log')
        file_mode = 'a'
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(process)-6d %(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=log_file,
        filemode=file_mode
    )
    logging.addLevelName(TRACE_LEVEL_NUM, 'TRACE')
    logging.Logger.trace = trace
    if verbosity != 'NONE':
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, verbosity))
        console.setFormatter(logging.Formatter('%(relativeCreated)-10d %(module)-18s %(levelname)s: %(message)s'))
        logging.getLogger('').addHandler(console)
    logging.info('Logger initiated')


if __name__ == '__main__':
    args = get_arguments_parser().parse_args()
    conf = get_configuration(args.conf_path)
    configure_logger(conf['log_dir'], args.log_split, args.log_level, args.verbosity)
    try:
        args.exec_func(args, conf)
    except Exception as e:
        tbe = TracebackException.from_exception(e)
        logging.critical(' '.join(list(tbe.format())))
        sys.exit(1)
    logging.info('All done - terminating')
