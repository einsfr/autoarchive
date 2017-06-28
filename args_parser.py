import argparse

useindirasroot = (
    ('-ir', '--useindirasroot'),
    {
        'help': 'if input URL is a directory use out_dir/input_dir instead of out_dir only as output root',
        'dest': 'use_in_dir_as_root',
        'action': 'store_true'
    }
)

dirdepth = (
    ('-dd', '--dirdepth'),
    {
        'dest': 'dir_depth',
        'help': 'output directory tree depth',
        'type': int,
        'default': 0
    }
)

args_parser = argparse.ArgumentParser()
args_parser.add_argument(
    '-v', '--verbosity',
    help='verbosity level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL, NONE',
    type=str,
    choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NONE'],
    default='INFO'
)
args_parser.add_argument(
    '-l', '--loglevel',
    dest='log_level',
    help='file logging level: DEBUG, INFO, WARNING (DEFAULT), ERROR, CRITICAL',
    type=str,
    choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    default='INFO'
)
args_parser.add_argument(
    '-ls', '--logsplit',
    dest='log_split',
    help='split log file',
    action='store_true'
)
args_parser.add_argument(
    '-c', '--confpath',
    dest='conf_path',
    help='path to configuration file',
    type=str,
    default='config.json'
)
args_parser.add_argument(
    '-s', '--simulate',
    help='simulate command execution for test purposes - no changes will be made',
    action='store_true'
)

subparsers = args_parser.add_subparsers(dest='command', help='command')
subparsers.required = True

parser_run = subparsers.add_parser('run')
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
    *useindirasroot[0],
    **useindirasroot[1]
)
parser_run.add_argument(
    *dirdepth[0],
    **dirdepth[1]
)

parser_version = subparsers.add_parser('version')

parser_convert = subparsers.add_parser('convert')
parser_convert.add_argument(
    'input_url',
    help='input URL',
    type=str
)
parser_convert.add_argument(
    'profile',
    help='Conversion profile\'s name',
    type=str
)
parser_convert.add_argument(
    '-cv', '--converter',
    help='converter module name',
    type=str,
    default='basic'
)


def _convert_profilevar(value: str):
    splitted_value = value.split('=', 1)
    if len(splitted_value) == 1:
        return splitted_value, None
    else:
        return splitted_value

parser_convert.add_argument(
    '-pv', '--profilevar',
    help='profile variables',
    action='append',
    type=_convert_profilevar,
)

parser_convert.add_argument(
    *useindirasroot[0],
    **useindirasroot[1]
)
parser_convert.add_argument(
    *dirdepth[0],
    **dirdepth[1]
)
