import logging
import os
import re
import pprint

from action import get_action_class
from dispatcher import PolicyViolationException


class BasicDispatcher:

    def __init__(self, conf: dict, rules_set: dict, input_url: str, dir_depth: int, use_in_dir_as_root: bool,
                 simulate: bool, **kwargs):
        self._conf = conf
        self._patterns = rules_set['patterns']
        self._policy = rules_set['policy']
        self._dir_depth = dir_depth
        self._input_url = input_url
        self._use_in_dir_as_root = use_in_dir_as_root
        self._simulate = simulate

        self._patterns_cache = []
        self._action_cache = {}  # ACTIONS ARE CACHEABLE - DO NOT FORGET IT - THEY'RE USED MORE THAN ONCE

    def dispatch(self):
        if self._simulate:
            logging.warning('--- THIS IS A SIMULATION - NO CHANGES WILL BE MADE ---')
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

    def _get_matching_patterns(self, in_path: str) -> list:
        if not self._patterns_cache:
            logging.debug('Filling rules set patterns cache...')
            self._fill_patterns_cache()
            logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))
        return [(a, ap) for r, a, ap in self._patterns_cache if r.match(in_path) is not None]

    def _get_action(self, action_id: str):
        try:
            return self._action_cache[action_id]
        except KeyError:
            logging.debug('Action cache miss - importing {}...'.format(action_id))
            action = get_action_class(action_id)(self._conf, self._simulate)
            self._action_cache[action_id] = action
            return action

    def _dispatch_file(self):
        self._input_url = os.path.abspath(self._input_url)
        self._dispatch_file_dir_common(self._input_url, self._conf['out_dir'])

    def _dispatch_file_dir_common(self, in_path: str, out_dir: str):
        logging.info('Searching for matching patterns in rules set for "{}"...'.format(in_path))
        patterns = self._get_matching_patterns(in_path)
        if not patterns:
            logging.info('No matches were found')
            if self._policy == 'skip':
                return
            elif self._policy == 'warning':
                logging.warning('No matches were found for "{}"'.format(in_path))
            elif self._policy == 'error':
                raise PolicyViolationException('No matches were found for "{}"'.format(in_path))
            else:
                raise ValueError('Unknown policy: {}'.format(self._policy))
        logging.info('Found {} matching pattern(s)'.format(len(patterns)))
        logging.debug('Matches: {}'.format(patterns))
        for n, p in enumerate(patterns):
            action_id, action_params = p
            logging.info('Performing action "{}" for pattern {} of {}'.format(action_id, n + 1, len(patterns)))
            self._get_action(action_id).run(in_path, action_params, out_dir)

    def _dispatch_directory(self):
        self._input_url = os.path.abspath(self._input_url)
        if self._use_in_dir_as_root:
            logging.debug('Including input directory to output path...')
            out_base_dir = os.path.join(self._conf['out_dir'], os.path.split(self._input_url)[1])
        else:
            out_base_dir = self._conf['out_dir']

        logging.debug('Building file list...')
        dir_list = []
        input_root_len = len(self._input_url)
        for path, dirs, files in os.walk(self._input_url):
            logging.debug('Path: {} Dirs: {} Files: {}'.format(path, dirs, files))
            if len(files):
                dir_list.append({'dir': path[input_root_len + 1:], 'files': files})

        dir_count = len(dir_list)
        file_count = 0
        for d in dir_list:
            file_count += len(d['files'])
        logging.debug('Found {} files(s) in {} directory(ies)'.format(file_count, dir_count))

        processed_files_count = 0
        processed_errors = []
        if self._dir_depth < 0:
            logging.debug('Creating output directory "{}"...'.format(out_base_dir))
            if not self._simulate:
                os.makedirs(out_base_dir, exist_ok=True)
        for d in dir_list:
            if self._dir_depth > 0:
                path = d['dir']
                path_list = []
                while True:
                    head, tail = os.path.split(path)
                    path = head
                    if tail:
                        path_list.append(tail)
                    if not head:
                        break
                if len(path_list) == 0:
                    out_dir = out_base_dir
                else:
                    if len(path_list) < self._dir_depth:
                        out_dir = os.path.join(out_base_dir, *path_list[::-1])
                    else:
                        out_dir = os.path.join(out_base_dir, *path_list[:-self._dir_depth - 1:-1])
                    logging.debug('Creating output directory "{}"...'.format(out_dir))
                    if not self._simulate:
                        os.makedirs(out_dir, exist_ok=True)
            else:
                out_dir = out_base_dir
            for f in d['files']:
                input_path = os.path.join(self._input_url, d['dir'], f)
                processed_files_count += 1
                logging.info('Processing file {} of {}: "{}"'.format(processed_files_count, file_count, input_path))
                try:
                    self._dispatch_file_dir_common(input_path, out_dir)
                except PolicyViolationException as e:
                    raise e
                except Exception as e:
                    processed_errors.append((input_path, e))
        errors_count = len(processed_errors)
        if errors_count:
            logging.warning('Finished with {} error(s)'.format(errors_count))
        else:
            logging.info('Finished without errors')
