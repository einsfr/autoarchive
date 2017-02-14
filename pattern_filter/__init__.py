

class AbstractPatternFilter:

    def __init__(self, conf: dict):
        self._conf = conf

    def filter(self, input_url: str, filter_params: dict) -> bool:
        raise NotImplementedError
