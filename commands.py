import logging

from dispatcher import get_dispatcher_class
from rules_provider import get_rules_provider_class
from args import get_args


def command_run() -> None:
    logging.info('Starting "run" command...')
    args = get_args()
    rules_provider = get_rules_provider_class(args.rules_provider)()
    rules_set = rules_provider.get_rules(args.rules_set)
    if not rules_set:
        raise ValueError('Rules set can\'t be empty')
    if type(rules_set) != dict:
        raise TypeError('Rules set must be a dictionary')
    logging.debug('Rules set ready')
    logging.debug('Starting dispatcher...')
    get_dispatcher_class(args.dispatcher)(rules_set).dispatch()
