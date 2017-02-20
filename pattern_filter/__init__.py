from utils.module_import import get_class


def get_pattern_filter_class(filter_id: str):
    return get_class('pattern filter', filter_id)


class AbstractPatternFilter:

    def filter(self, input_url: str, filter_params: dict) -> bool:
        raise NotImplementedError
