import logging

from .factory import FFmpegFactory

logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')

factory_class = FFmpegFactory
factory_args = {}

_factory = None


def get_ffmpeg_factory():
    global _factory
    if _factory is None:
        _factory = factory_class(**factory_args)
    return _factory
