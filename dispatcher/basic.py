import logging
import os
import re
import pprint

from action import get_action_class


class BasicDispatcher:

    def __init__(self, conf: dict, rules_set: dict, input_url: str, dir_depth: int, use_in_dir_as_root: bool, **kwargs):
        self._conf = conf
        self._patterns = rules_set['patterns']
        self._policy = rules_set['policy']
        self._dir_depth = dir_depth
        self._input_url = input_url
        self._use_in_dir_as_root = use_in_dir_as_root

        self._patterns_cache = []
        self._action_cache = {}  # ACTIONS ARE CACHEABLE - DO NOT FORGET IT - THEY'RE USED MORE THAN ONCE

    def dispatch(self):
        if os.path.isfile(self._input_url):
            logging.info('Dispatching input URL as a file...')
            self._dispatch_file()
        elif os.path.isdir(self._input_url):
            logging.info('Dispatching input URL as a directory...')
            self._dispatch_directory()
        else:
            raise ValueError('Basic dispatcher supports only files and directories as input')

    def _fill_patterns_cache(self):
        self._patterns_cache = []
        for reg_exp, action, action_params in self._patterns:
            self._patterns_cache.append((re.compile(reg_exp, re.IGNORECASE), action, action_params))

    def _get_matching_patterns(self) -> list:
        if not self._patterns_cache:
            logging.debug('Filling rules set patterns cache...')
            self._fill_patterns_cache()
            logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))
        return [(a, ap) for r, a, ap in self._patterns_cache if r.match(self._input_url) is not None]

    def _get_action(self, action_id: str):
        try:
            return self._action_cache[action_id]
        except KeyError:
            logging.debug('Action cache miss - importing {}...'.format(action_id))
            action = get_action_class(action_id)(self._conf)
            self._action_cache[action_id] = action
            return action

    def _dispatch_file(self):
        self._input_url = os.path.abspath(self._input_url)
        logging.info('Searching for matching patterns in rules set for {}...'.format(self._input_url))
        patterns = self._get_matching_patterns()
        if not patterns:
            logging.info('No matches were found')
            return
        logging.info('Found {} matching pattern(s)'.format(len(patterns)))
        logging.debug('Matches: {}'.format(patterns))
        for n, p in enumerate(patterns):
            action_id, action_params = p
            logging.info('Performing action "{}" for pattern {} of {}'.format(action_id, n + 1, len(patterns)))
            self._get_action(action_id).run(self._input_url, action_params)

    def _dispatch_directory(self):
        self._input_url = os.path.abspath(self._input_url)
        if self._use_in_dir_as_root:
            logging.debug('Including input directory to output path...')
            out_rel_list = [os.path.split(self._input_url)[1]]
        else:
            out_rel_list = []

