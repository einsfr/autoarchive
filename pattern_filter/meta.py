import logging

from pattern_filter import AbstractPatternFilter


class MetadataPatternFilter(AbstractPatternFilter):

    def filter(self, input_url: str, filter_params: dict) -> bool:
        pass
