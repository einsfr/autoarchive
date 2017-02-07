import os
import logging
import sys
from datetime import datetime

from args import get_arguments_parser
from configuration import get_configuration


BASE_DIR = os.path.dirname(__file__)


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
    if verbosity != 'NONE':
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, verbosity))
        console.setFormatter(logging.Formatter('%(relativeCreated)-4d %(module)-16s %(levelname)s: %(message)s'))
        logging.getLogger('').addHandler(console)
    logging.info('Logger initiated')


if __name__ == '__main__':
    args = get_arguments_parser().parse_args()
    conf = get_configuration(args.conf_path)
    configure_logger(conf['log_dir'], args.log_split, args.log_level, args.verbosity)
    try:
        args.exec_func(args, conf)
    except Exception as e:
        logging.critical(str(e))
        sys.exit(1)
    logging.info('All done - terminating')
