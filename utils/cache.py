import hashlib
import logging
from collections import OrderedDict


class CacheMissException(RuntimeWarning):
    pass


class HashCacheMixin:

    def __init__(self, *args, cache_size: int, **kwargs):
        self._cache = OrderedDict()
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0

    @staticmethod
    def get_hashed_id(item_id: str) -> str:
        return hashlib.sha1(item_id.encode()).hexdigest()

    def to_cache(self, item_id: str, item):
        self._cache[self.get_hashed_id(item_id)] = item
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def from_cache(self, item_id: str):
        try:
            value = self._cache[self.get_hashed_id(item_id)]
        except KeyError:
            logging.debug('Cache miss')
            raise CacheMissException
        else:
            logging.debug('Cache hit')
            return value

    def cache_stats(self):
        total_requests = self._cache_hits + self._cache_misses
        return self._cache_hits, self._cache_misses, total_requests, self._cache_hits / total_requests
