import logging

from dispatcher import get_dispatcher_class
from rules_provider import get_rules_provider_class


def command_run(args, conf: dict) -> None:
    logging.info('Starting "run" command...')
    rules_provider = get_rules_provider_class(args.rules_provider)()
    rules_set = rules_provider.get_rules(args.rules_set)
    if not rules_set:
        raise ValueError('Rules set can\'t be empty')
    if type(rules_set) != dict:
        raise TypeError('Rules set must be a dictionary')
    args_dict = vars(args)
    args_dict['rules_set'] = rules_set
    logging.debug('Rules set ready')
    logging.debug('Starting dispatcher...')
    dispatcher_class = get_dispatcher_class(args.dispatcher)
    dispatcher = dispatcher_class(conf, **args_dict)
    dispatcher.dispatch()
