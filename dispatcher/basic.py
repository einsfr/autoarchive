""" Модуль с классом `BasicDispatcher`

"""

import logging
import os
import re
import pprint

from action import get_action_class
from pattern_filter import get_pattern_filter_class
from dispatcher import PolicyViolationException, ActionRunException, UnknownPolicyException
from utils.file_list import build_file_list


class BasicDispatcher:
    """ Класс, описывающий простой диспетчер

    Получает все необходимые для работы параметры из конфигурации приложения и аргументов командной строки. Для всех
    действий, с которыми будет работать диспетчер, будут создаваться соответствущие объекты - по одному для каждого
    типа действия - поэтому используется внутренный кэш для сохранения подобных объектов. Та же ситуация и с фильтрами.
    """

    def __init__(self, input_url: str, rules_set: dict, conf_out_dir: str, dir_depth: int, use_in_dir_as_root: bool,
                 simulate: bool):
        """

        Args:
            rules_set: Набор правил для обработки
            input_url: Входной URL
            conf_out_dir: Корневая выходная папка
            dir_depth: Глубина дерева выходных папок
            use_in_dir_as_root: Использовать ли входную папку (если URL - папка) в качестве корня для выхода
            simulate: Если это симуляция - никаких реальных изменений происходить не будет
        """

        self._policy = rules_set['policy']
        self._no_match_files = []
        self._conf_out_dir = conf_out_dir
        self._dir_depth = dir_depth
        self._use_in_dir_as_root = use_in_dir_as_root
        self._simulate = simulate

        self._input_url = os.path.abspath(input_url)
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
        """ Компилирует все регулярные выражения из набора правил
        """
        logging.debug('Filling rules set patterns cache...')
        for reg_exp, *p in self._patterns:
            self._patterns_cache.append((re.compile(reg_exp, re.IGNORECASE), reg_exp, *p))
        logging.debug('Rules set patterns cache:\r\n{}'.format(pprint.pformat(self._patterns_cache)))

    def dispatch(self):
        """ Запускает обработку

        Raises:
            ValueError: Если по входному пути находится неподходящий объект
        """
        if self._simulate:
            logging.warning('--- THIS IS A SIMULATION - NO CHANGES WILL BE MADE ---')
        if self._input_is_a_file:
            self._input_base_dir, filename = os.path.split(self._input_url)
            self._dir_list = [{'rel_in_dir': '', 'files': [filename]}]
            self._file_count = 1
        elif self._input_is_a_dir:
            self._input_base_dir = self._input_url
            self._dir_list, self._file_count = build_file_list(self._input_url)
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
        """ Обрабатывает один файл

        Отвечая на вопрос "Зачем передавать отдельно путь к папке и отдельно - путь к файлу в ней же" скажу - всё равно
        и то и другое присутствует в точке вызова - зачем тратить время на то, чтобы отделять название файла от пути
        к папке ещё раз?

        Args:
            rel_in_dir: относительный путь к папке, содержащей обрабатываемый файл
            rel_in_path: относительный путь к обрабатываемому файлу

        Raises:
            PolicyViolationException: при использовании политики `error` и отсутствии для какого-либо файла
                соответствующего ему действия
            UnknownPolicyException: при попытке использовани политики, неизвестной диспетчеру
        """
        logging.debug('Base input directory: "{}"'.format(self._input_base_dir))
        logging.info('Searching for matching patterns in rules set for "{}"...'.format(rel_in_path))
        patterns = self._get_matching_patterns(rel_in_path)
        if not patterns:
            logging.info('No matches were found')
            if self._policy == 'skip':
                return
            elif self._policy == 'warning':
                self._no_match_files.append(rel_in_path)
                return
            elif self._policy == 'error':
                raise PolicyViolationException('No matches were found for "{}"'.format(rel_in_path))
            else:
                raise UnknownPolicyException(self._policy)

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
                dir_name = os.path.split(self._input_base_dir)[1]
                if dir_name:
                    rel_out_dir_list.append(dir_name)
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
                out_dir,
                self._simulate
            )

    def _get_matching_patterns(self, in_path: str) -> list:
        """ Поиск правил, соответствующих пути в `in_path`

        Args:
            in_path: **относительный** путь к файлу, для которого ищется соответствие

        Returns:
            Список вида::

                [
                    (
                        регулярное выражение, по которому произошло совпадение,
                        {
                            параметр обработки соответствия (фильтры, например)...
                        },
                        название действия,
                        {
                            параметры действия...
                        }
                    )
                ]

        """
        return [p for r, *p in self._patterns_cache if r.match(in_path) is not None]

    def _get_action(self, action_id: str):
        """ Возвращает объект с действием

        Сначала попытается найти соответствующий объект в кэше экземпляра, если же его там нет - создаст и сохранит.

        Returns:
            Экземпляр класса, описывающего действие
        """
        try:
            return self._action_cache[action_id]
        except KeyError:
            logging.debug('Action cache miss - importing {}...'.format(action_id))
            action = get_action_class(action_id)()
            self._action_cache[action_id] = action
            return action

    def _get_filter(self, filter_id: str):
        """ Возвращает объект с фильтром

        Сначала попытается найти соответствующий объект в кэше экземпляра, если же его там нет - создаст и сохранит.

        Returns:
            Экземпляр класса, описывающего фильтр
        """
        try:
            return self._filter_cache[filter_id]
        except KeyError:
            logging.debug('Filter cache miss - importing {}...'.format(filter_id))
            filter_obj = get_pattern_filter_class(filter_id)()
            self._filter_cache[filter_id] = filter_obj
            return filter_obj

    def _filter_patterns(self, input_url: str, patterns: list) -> list:
        """ Производит фильтрацию совпадений имён файлов по регулярному выражению

        Помимо собственном фильтрации обрабатывает параметр совпадения `passthrough` - если он присутствует и его
        значение False - просто удаляет все дальнейшие совпадения.

        Args:
            input_url: **абсолютный** путь к файлу, для которого нашлись совпадения
            patterns: список совпадений

        Returns:
            Возвращает отфильтрованный список совпадений. Формат соответствует формату возвращаемого значения
            в `_get_matching_patterns`
        """
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
