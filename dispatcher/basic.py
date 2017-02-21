import logging
import os
import re
import pprint

from action import get_action_class
from pattern_filter import get_pattern_filter_class
from dispatcher import PolicyViolationException, ActionRunException
from args import get_args
from configuration import get_configuration


class BasicDispatcher:

    def __init__(self, rules_set: dict):
        args = get_args()

        self._policy = rules_set['policy']
        self._no_match_files = []
        self._conf_out_dir = get_configuration()['out_dir']
        self._dir_depth = args.dir_depth
        self._use_in_dir_as_root = args.use_in_dir_as_root
        self._simulate = args.simulate

        self._input_url = os.path.abspath(args.input_url)
        self._input_is_a_file = os.path.isfile(self._input_url)
        self._input_is_a_dir = os.path.isdir(self._input_url)

        self._patterns = rules_set['patterns']
        self._patterns_cache = []
        self._fill_patterns_cache()

        self._action_cache = {}  # ACTIONS ARE CACHEABLE - DO NOT FORGET IT - THEY'RE USED MORE THAN ONCE
        self._filter_cache = {}  # FILTERS ARE CACHEABLE - DO NOT FORGET IT - THEY'RE USED MORE THAN ONCE

    def _fill_patterns_cache(self):
        logging.debug('Filling rules set patterns cache...')
        for reg_exp, *p in self._patterns:
            self._patterns_cache.append((re.compile(reg_exp, re.IGNORECASE), reg_exp, *p))
        logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))

    def dispatch(self):
        if self._simulate:
            logging.warning('--- THIS IS A SIMULATION - NO CHANGES WILL BE MADE ---')
        if self._input_is_a_file:
            raise NotImplementedError  # TODO: FIX
        elif self._input_is_a_dir:
            if self._use_in_dir_as_root:
                logging.debug('Including input directory to output path...')
                rel_out_dir = (os.path.split(self._input_url)[1])
            else:
                rel_out_dir = ''

            logging.debug('Building file list...')
            input_root_len = len(self._input_url)
            dir_list = []
            file_count = 0
            for path, dirs, files in os.walk(self._input_url):
                if len(files):
                    dir_list.append({'rel_dir': path[input_root_len + 1:], 'files': files})
                    file_count += len(files)
            logging.debug('Found {} files(s) in {} directory(ies)'.format(file_count, len(dir_list)))

        else:
            raise ValueError('Basic dispatcher supports only files and directories as input')

    def _get_matching_patterns(self, in_path: str) -> list:
        return [p for r, *p in self._patterns_cache if r.match(in_path) is not None]

    def _get_action(self, action_id: str):
        try:
            return self._action_cache[action_id]
        except KeyError:
            logging.debug('Action cache miss - importing {}...'.format(action_id))
            action = get_action_class(action_id)()
            self._action_cache[action_id] = action
            return action

    def _get_filter(self, filter_id: str):
        try:
            return self._filter_cache[filter_id]
        except KeyError:
            logging.debug('Filter cache miss - importing {}...'.format(filter_id))
            filter_obj = get_pattern_filter_class(filter_id)()
            self._filter_cache[filter_id] = filter_obj
            return filter_obj

    def _dispatch_file_dir_common(self, in_path: str, out_dir_relative: str):
        logging.info('Searching for matching patterns in rules set for "{}"...'.format(in_path))
        patterns = self._get_matching_patterns(in_path)
        if not patterns:
            logging.info('No matches were found')
            if self._policy == 'skip':
                return
            elif self._policy == 'warning':
                self._no_match_files.append(in_path)
            elif self._policy == 'error':
                raise PolicyViolationException('No matches were found for "{}"'.format(in_path))
            else:
                raise ValueError('Unknown policy: {}'.format(self._policy))
        logging.debug('Matches: {}'.format(patterns))
        filtered_patterns = self._filter_patterns(in_path, patterns)
        for n, p in enumerate(filtered_patterns):
            action_id = p[2]
            action_params = p[3]
            logging.info(
                'Pattern {} of {}: performing action: {}; action parameters: {}...'.format(
                    n + 1, len(filtered_patterns), action_id, action_params
                )
            )
            action = self._get_action(action_id)
            logging.debug('Using action object {}'.format(action))
            if 'out_dir' in action_params and action_params['out_dir']:
                out_dir = os.path.abspath(os.path.join(self._conf_out_dir, action_params['out_dir'], out_dir_relative))
            else:
                out_dir = os.path.join(self._conf_out_dir, out_dir_relative)
            action.run(in_path, action_params, out_dir)

    def _filter_patterns(self, input_url: str, patterns: list) -> list:
        result = []
        for n, p in enumerate(patterns):
            pattern_opts = p[1]

            if 'filters' in pattern_opts:
                if not all(
                        [self._get_filter(filter_id).filter(input_url, filter_params)
                         for filter_id, filter_params in pattern_opts['filters'].items()]
                ):
                    continue

            if 'passthrough' in pattern_opts:
                if not pattern_opts['passthrough']:
                    result.append(p)
                    break

            result.append(p)
        if len(result) != len(patterns):
            logging.debug('Matches after filtering: {}'.format(result))
        return result

    def _no_matches_warning(self):
        if self._policy == 'warning' and self._no_match_files:
            logging.warning(
                'Matching patterns were not found for these files ({}):\r\n{}'.format(
                    len(self._no_match_files),
                    '\r\n'.join(self._no_match_files)
                )
            )

    def _dispatch_directory(self):

        processed_files_count = 0
        processed_errors = []
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
                except ActionRunException as e:
                    processed_errors.append((input_path, e))
        self._no_matches_warning()
        errors_count = len(processed_errors)
        if errors_count:
            logging.warning('Finished with {} error(s):\r\n{}'.format(
                errors_count,
                '\r\n'.join(['{}: {} {}'.format(pe[0], type(pe[1]), str(pe[1])) for pe in processed_errors])
            ))
        else:
            logging.info('Finished without errors')
