import logging
import re

from ffmpeg.metadata_collector import FFprobeMetadataCollector, FFprobeMetadataResult
from ffmpeg import get_ffmpeg_factory
from ffmpeg.exceptions import UnknownFilterSelector, UnknownMetadataParameter, WrongConditionType, UnknownOperator,\
    ConditionPairProcessingException


class FFprobeMetadataFilter:

    STREAM_SELECTOR_RE = r'^stream:(v|a):(\d+)$'
    COUNT_SELECTOR_RE = r'^count:(v|a)$'

    def __init__(self):
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ff_metadata_collector = get_ffmpeg_factory().get_ffprobe_metadata_collector(FFprobeMetadataCollector)
        self._stream_selector_re = re.compile(self.STREAM_SELECTOR_RE, re.IGNORECASE)
        self._count_selector_re = re.compile(self.COUNT_SELECTOR_RE, re.IGNORECASE)

    def filter(self, input_url: str, filter_params: dict) -> bool:
        logging.debug('Filtering started with parameters: {}'.format(filter_params))
        input_meta = self._ff_metadata_collector.get_metadata(input_url)
        for selector, selector_data in filter_params.items():
            logging.debug('Processing selector "{}"...'.format(selector))
            result = False
            if selector.lower() == 'format':
                logging.debug('This is a format selector')
                result = self._filter_format(input_meta, selector_data)
            else:
                matched = False

                match = self._stream_selector_re.match(selector)
                if match:
                    logging.debug('This is a stream selector')
                    matched = True
                    result = self._filter_stream(input_meta, selector_data)

                match = self._count_selector_re.match(selector)
                if match:
                    logging.debug('This is a count selector')
                    matched = True
                    result = self._filter_count(input_meta, selector_data)

                if not matched:
                    raise UnknownFilterSelector(selector)
            if result:
                logging.debug('Passed')
            else:
                logging.debug('Failed')
                return False
        logging.debug('Filter passed')
        return True

    def _filter_format(self, input_meta: FFprobeMetadataResult, selector_data: dict) -> bool:
        format_data = input_meta.format
        for param, condition in selector_data.items():
            try:
                param_value = format_data[param]
            except KeyError:
                raise UnknownMetadataParameter(param)
            if not self._process_condition(param_value, condition):
                return False
        return True

    def _filter_stream(self, input_meta: FFprobeMetadataResult, conditions) -> bool:
        return True

    def _filter_count(self, input_meta: FFprobeMetadataResult, conditions) -> bool:
        return True

    def _process_condition(self, value, condition) -> bool:
        t = type(condition)
        if t in [int, float, str]:
            logging.debug('Condition a simple value')
            try:
                return value == t(condition)
            except ValueError as e:
                raise ConditionPairProcessingException(value, 'eq', condition) from e
        elif t == list:
            if type(condition[0]) == str:
                logging.debug('Condition is a [operator, value] list')
                return self._process_cond_pair(value, *condition)
            elif type(condition[0]) == list:
                logging.debug('Condition is a list of [operator, value] lists')
                return all(map(lambda x: self._process_cond_pair(value, *x)))
        else:
            raise WrongConditionType(type(condition))

    def _process_cond_pair(self, value_left, operator: str, value_right) -> bool:
        operator = operator.lower()
        try:
            value_left_typed = type(value_right)(value_left)
        except ValueError as e:
            raise ConditionPairProcessingException(value_left, operator, value_right) from e
        try:
            if operator == 'eq':
                return value_left_typed == value_right
            elif operator == 'neq':
                return value_left_typed != value_right
            elif operator == 'gt':
                return value_left_typed > value_right
            elif operator == 'gte':
                return value_left_typed >= value_right
            elif operator == 'lt':
                return value_left_typed < value_right
            elif operator == 'lte':
                return value_left_typed <= value_right
            else:
                raise UnknownOperator(operator)
        except UnknownOperator as e:
            raise e
        except Exception as e:
            raise ConditionPairProcessingException(value_left_typed, operator, value_right) from e
