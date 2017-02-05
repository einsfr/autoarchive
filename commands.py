import logging

from dispatcher import get_dispatcher
from rules_provider import get_rules_provider


def command_run(args, conf: dict) -> None:
    logging.info('Starting "run" command...')
    dispatcher = get_dispatcher(args.dispatcher)
    rules_provider = get_rules_provider(args.rules_provider)
    rules_set = rules_provider.get_rules(args.rules_set)
    if not rules_set:
        raise ValueError('Rules set can\'t be empty')
    if type(rules_set) != dict:
        raise TypeError('Rules set must be a dictionary')
    logging.info('Rules set ready')
    logging.debug('Dumping rules set:\r\n{}'.format(rules_set))
    logging.info('Starting dispatcher...')
    dispatcher.dispatch(args.input, rules_set)
