import argparse

import commands


def get_arguments_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbosity',
        help='verbosity level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL, NONE',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NONE'],
        default='WARNING'
    )
    parser.add_argument(
        '-l', '--loglevel',
        dest='log_level',
        help='file logging level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='WARNING'
    )
    parser.add_argument(
        '-ls', '--logsplit',
        dest='log_split',
        help='split log file',
        action='store_true'
    )
    parser.add_argument(
        '-c', '--confpath',
        dest='conf_path',
        help='path to configuration file',
        type=str,
        default='config.json'
    )

    subparsers = parser.add_subparsers(dest='command', help='command')
    parser_run = subparsers.add_parser('run')
    parser_run.set_defaults(exec_func=commands.command_run)

    return parser
