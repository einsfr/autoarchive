import os
import logging
import sys

from datetime import datetime
from traceback import TracebackException

from args import get_arguments_parser
from configuration import get_configuration


BASE_DIR = os.path.dirname(__file__)


def configure_logger(log_dir: str, log_split: bool, log_level: str, verbosity: str) -> None:
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
    file.setFormatter(logging.Formatter('%(process)-6d %(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(file)

    if verbosity != 'NONE':
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, verbosity))
        console.setFormatter(logging.Formatter('%(relativeCreated)-10d %(module)-18s %(levelname)s: %(message)s'))
        logger.addHandler(console)

    logging.debug('Logger initiated')


if __name__ == '__main__':
    os.chdir(BASE_DIR)
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
