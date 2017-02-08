import logging
import os
import re
import pprint

from action import get_action_class


class BasicDispatcher:

    def __init__(self, conf: dict, rules_set: dict, dir_depth: int):
        self._conf = conf
        self._patterns = rules_set['patterns']
        self._policy = rules_set['policy']
        self._dir_depth = dir_depth
        self._patterns_cache = []
        self._action_cache = {}

    def dispatch(self, input_url: str):
        if os.path.isfile(input_url):
            logging.info('Dispatching input URL as a file...')
            self._dispatch_file(input_url)
        elif os.path.isdir(input_url):
            logging.info('Dispatching input URL as a directory...')
        else:
            raise ValueError('Basic dispatcher supports only files and directories as input')

    def _fill_patterns_cache(self):
        self._patterns_cache = []
        for reg_exp, action, action_params in self._patterns:
            self._patterns_cache.append((re.compile(reg_exp, re.IGNORECASE), action, action_params))

    def _get_matching_patterns(self, input_url: str) -> list:
        if not self._patterns_cache:
            logging.info('Filling rules set patterns cache...')
            self._fill_patterns_cache()
            logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))
        return [(a, ap) for r, a, ap in self._patterns_cache if r.match(input_url) is not None]

    def _get_action(self, action_id: str):
        try:
            return self._action_cache[action_id]
        except KeyError:
            logging.debug('Action cache miss - importing {}...'.format(action_id))
            action = get_action_class(action_id)(self._conf)
            self._action_cache[action_id] = action
            return action

    def _dispatch_file(self, input_url: str):
        logging.info('Searching for matching patterns in rules set for {}...'.format(input_url))
        patterns = self._get_matching_patterns(input_url)
        if not patterns:
            logging.info('No matches were found')
            return
        logging.info('Found {} matching pattern(s)'.format(len(patterns)))
        logging.debug('Matches: {}'.format(patterns))
        for n, p in enumerate(patterns):
            action_id, action_params = p
            logging.info('Performing action "{}" for pattern {}'.format(action_id, n + 1))
            self._get_action(action_id).run(input_url, action_params)
