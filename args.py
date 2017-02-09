import argparse

import commands


def get_arguments_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbosity',
        help='verbosity level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL, NONE',
        type=str,
        choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NONE'],
        default='INFO'
    )
    parser.add_argument(
        '-l', '--loglevel',
        dest='log_level',
        help='file logging level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL',
        type=str,
        choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
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
    parser.add_argument(
        '-s', '--simulate',
        help='simulate command execution for test purposes - no changes will be made',
        action='store_true'
    )

    subparsers = parser.add_subparsers(dest='command', help='command')
    subparsers.required = True

    parser_run = subparsers.add_parser('run')
    parser_run.set_defaults(exec_func=commands.command_run)
    parser_run.add_argument(
        'input_url',
        help='input URL',
        type=str
    )
    parser_run.add_argument(
        'rules_set',
        help='rules set path',
        type=str
    )
    parser_run.add_argument(
        '-d', '--dispatcher',
        help='dispatcher module name',
        type=str,
        default='basic'
    )
    parser_run.add_argument(
        '-r', '--rulesprovider',
        help='rules provider module name',
        dest='rules_provider',
        type=str,
        default='json'
    )
    parser_run.add_argument(
        '-ir', '--useindirasroot',
        help='if input URL is a directory use out_dir/input_dir instead of out_dir only as output root',
        dest='use_in_dir_as_root',
        action='store_true'
    )
    parser_run.add_argument(
        '-dd', '--dirdepth',
        dest='dir_depth',
        help='output directory tree depth',
        type=int,
        default=0
    )

    return parser
