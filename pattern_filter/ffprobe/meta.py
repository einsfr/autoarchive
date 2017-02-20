from ffmpeg import get_ffmpeg_factory
from ffmpeg.metadata_filter import FFprobeMetadataFilter
from pattern_filter import AbstractPatternFilter


class FfprobeMetaPatternFilter(AbstractPatternFilter):

    def __init__(self):
        super().__init__()
        self._ff_meta_filter = get_ffmpeg_factory().get_ffprobe_metadata_filter(FFprobeMetadataFilter)

    def filter(self, input_url: str, filter_params: dict) -> bool:
        return self._ff_meta_filter.filter(input_url, filter_params)
