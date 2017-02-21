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

        self._no_match_files = []
        self._input_base_dir = ''
        self._dir_list = []
        self._file_count = 0

    def _fill_patterns_cache(self):
        logging.debug('Filling rules set patterns cache...')
        for reg_exp, *p in self._patterns:
            self._patterns_cache.append((re.compile(reg_exp, re.IGNORECASE), reg_exp, *p))
        logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))

    def dispatch(self):
        if self._simulate:
            logging.warning('--- THIS IS A SIMULATION - NO CHANGES WILL BE MADE ---')
        if self._input_is_a_file:
            self._input_base_dir, filename = os.path.split(self._input_url)
            self._dir_list = [{'rel_in_dir': '', 'files': [filename]}]
            self._file_count = 1
        elif self._input_is_a_dir:
            self._input_base_dir = self._input_url
            logging.debug('Building file list...')
            for path, dirs, files in os.walk(self._input_url):
                if len(files):
                    self._dir_list.append({'rel_in_dir': path[len(self._input_url) + 1:], 'files': files})
                    self._file_count += len(files)
            logging.debug('Found {} files(s) in {} directory(ies)'.format(self._file_count, len(self._dir_list)))
        else:
            raise ValueError('Basic dispatcher supports only files and directories as input')

        processed_files_count = 0
        processed_errors = []
        for d in self._dir_list:
            for f in d['files']:
                rel_in_path = os.path.join(d['rel_in_dir'], f)
                logging.info('Processing file {} of {}: "{}"...'.format(
                    processed_files_count + 1, self._file_count, rel_in_path))
                try:
                    self._dispatch(d['rel_in_dir'], rel_in_path)
                except PolicyViolationException as e:
                    raise e
                except ActionRunException as e:
                    processed_errors.append((rel_in_path, e))
                processed_files_count += 1
        if self._no_match_files and self._policy == 'warning':
            logging.warning(
                'Matching patterns were not found for these files ({}):\r\n{}'.format(
                    len(self._no_match_files),
                    '\r\n'.join(self._no_match_files)
                )
            )
        errors_count = len(processed_errors)
        if errors_count:
            logging.warning('Finished with {} error(s):\r\n{}'.format(
                errors_count,
                '\r\n'.join(['{}: {} {}'.format(pe[0], type(pe[1]), str(pe[1])) for pe in processed_errors])
            ))
        else:
            logging.info('Finished without errors')

    def _dispatch(self, rel_in_dir: str, rel_in_path: str):
        logging.debug('Base input directory: "{}"'.format(self._input_base_dir))
        logging.info('Searching for matching patterns in rules set for "{}"...'.format(rel_in_path))
        patterns = self._get_matching_patterns(rel_in_path)
        if not patterns:
            logging.info('No matches were found')
            if self._policy == 'skip':
                return
            elif self._policy == 'warning':
                self._no_match_files.append(rel_in_path)
            elif self._policy == 'error':
                raise PolicyViolationException('No matches were found for "{}"'.format(rel_in_path))
            else:
                raise ValueError('Unknown policy: {}'.format(self._policy))

        logging.debug('Matches: {}'.format(patterns))
        abs_in_path = os.path.join(self._input_base_dir, rel_in_path)
        filtered_patterns = self._filter_patterns(abs_in_path, patterns)
        for n, p in enumerate(filtered_patterns):
            action_id = p[2]
            action_params = p[3]
            logging.info(
                'Pattern {} of {}: performing action: {}; action parameters: {}...'.format(
                    n + 1, len(filtered_patterns), action_id, action_params
                )
            )

            logging.debug('Building output directory path...')
            rel_out_dir_list = []
            if self._input_is_a_dir and self._use_in_dir_as_root:
                rel_out_dir_list.append(self._input_base_dir)
            if 'out_dir' in action_params and action_params['out_dir']:
                rel_out_dir_list.append(action_params['out_dir'])

            dir_depth = action_params['dir_depth'] if 'dir_depth' in action_params else self._dir_depth
            logging.debug('Output directory depth is {}'.format(dir_depth))
            if rel_in_dir and dir_depth > 0:
                path = rel_in_dir
                path_list = []
                while True:
                    head, tail = os.path.split(path)
                    path = head
                    if tail:
                        path_list.append(tail)
                    if not head:
                        break
                logging.debug('Input path list: {}'.format(path_list))
                if len(path_list) > 0:
                    if len(path_list) < dir_depth:
                        logging.debug('Path list\'s length is less than output directory depth - using it all')
                        rel_out_dir_list.extend(path_list[::-1])
                    else:
                        path_list_slice = path_list[:-dir_depth - 1:-1]
                        logging.debug('Path list\'s length is greater than or equal to output directory depth - using '
                                      'slice: {}'.format(path_list_slice))
                        rel_out_dir_list.extend(path_list_slice)
            logging.debug('Output relative path list: {}'.format(rel_out_dir_list))
            out_dir = os.path.abspath(os.path.join(self._conf_out_dir, *rel_out_dir_list))
            logging.debug('Absolute output directory path: "{}"'.format(out_dir))

            logging.debug('Fetching action object...')
            action = self._get_action(action_id)
            logging.debug('Using action object {}'.format(action))
            action.run(
                abs_in_path,
                action_params,
                out_dir
            )

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
