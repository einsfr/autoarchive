import logging
import hashlib
from collections import OrderedDict

from ffmpeg.ffprobe import FFprobeFrameCommand


class AbstractInterlacedProgressiveSolver:

    IS_MIXED_OR_UNKNOWN = 0
    IS_INTERLACED_TFF = 1
    IS_INTERLACED_BFF = 2
    IS_PROGRESSIVE = 3

    DECISIONS = {
        IS_MIXED_OR_UNKNOWN: 'MIXED OR UNKNOWN',
        IS_INTERLACED_TFF: 'INTERLACED TFF',
        IS_INTERLACED_BFF: 'INTERLACED BFF',
        IS_PROGRESSIVE: 'PROGRESSIVE'
    }

    CACHE_SIZE = 10

    def __init__(self):
        self._cache = OrderedDict()

    def solve(self, input_url: str, video_stream_count: int) -> dict:
        raise NotImplementedError


class FFprobeInterlacedProgressiveSolver(AbstractInterlacedProgressiveSolver):

    READ_INTERVALS = '%+#10'

    def __init__(self, conf: dict):
        super().__init__()
        self._conf = conf

    def _to_cache(self, hash_id: str, item):
        self._cache[hash_id] = item
        if len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)

    def _from_cache(self, hash_id: str):
        return self._cache[hash_id]

    def _solve(self, total_count: int, tff_counf: int, bff_count: int, progressive_count: int) -> int:
        if tff_counf == total_count:
            return self.IS_INTERLACED_TFF
        if bff_count == total_count:
            return self.IS_INTERLACED_BFF
        if progressive_count == total_count:
            return self.IS_PROGRESSIVE
        return self.IS_MIXED_OR_UNKNOWN

    @staticmethod
    def _collect(v_frame_list: list) -> tuple:
        tff_count = 0
        bff_count = 0
        progressive_count = 0
        total_count = len(v_frame_list)
        for f in v_frame_list:
            if f['interlaced_frame'] == 1:
                if f['top_field_first'] == 1:
                    tff_count += 1
                else:
                    bff_count += 1
            else:
                if f['top_field_first'] == 1:
                    tff_count += 1
                else:
                    progressive_count += 1
        return total_count, tff_count, bff_count, progressive_count

    def solve(self, input_url: str, video_stream_count: int) -> dict:
        if video_stream_count == 0:
            raise ValueError('Input must have at least one video stream')
        input_hash = hashlib.sha1(input_url.encode()).hexdigest()
        try:
            cached_value = self._from_cache(input_hash)
        except KeyError:
            logging.debug('Solver cache miss')
            pass
        else:
            logging.debug('Solver cache hit')
            return cached_value
        logging.info('Decoding some frames to determine video streams field mode...')
        ffprobe_frame = FFprobeFrameCommand(self._conf['ffprobe_path'])
        result = {}
        for n in range(0, video_stream_count):
            v_frame_list = ffprobe_frame.exec(
                input_url,
                'v:{}'.format(n),
                self.READ_INTERVALS
            )['frames']
            stream_index = v_frame_list[0]['stream_index']
            collected = self._collect(v_frame_list)
            logging.debug('FFprobe result: total - {}, tff count - {}, bff count - {}, progressive count - {}'.format(
                *collected
            ))
            decision = self._solve(*collected)
            logging.info('Stream {} determined as {}'.format(stream_index, self.DECISIONS[decision]))
            result[stream_index] = decision
        self._to_cache(input_hash, result)
        return result
