import logging

from .factory import FFmpegFactory, FFprobeFactory
from .profile_loader import ProfileLoader

logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')


_ffmpeg_factory = None


def create_ffmpeg_factory(factory_class, *args, **kwargs):
    global _ffmpeg_factory
    _ffmpeg_factory = factory_class(*args, **kwargs)


def get_ffmpeg_factory():
    if _ffmpeg_factory is None:
        raise RuntimeError('Factory must be created with "create_ffmpeg_factory" function before using it')
    return _ffmpeg_factory


_ffprobe_factory = None


def create_ffprobe_factory(factory_class, *args, **kwargs):
    global _ffprobe_factory
    _ffprobe_factory = factory_class(*args, **kwargs)


def get_ffprobe_factory():
    if _ffprobe_factory is None:
        raise RuntimeError('Factory must be created with "create_ffprobe_factory" function before using it')
    return _ffprobe_factory


_profile_loader = None


def create_profile_loader(loader_class, *args, **kwargs):
    global _profile_loader
    _profile_loader = loader_class(*args, **kwargs)


def get_profile_loader():
    if _profile_loader is None:
        raise RuntimeError('Profile loader must be created with "create_profile_loader" function before using it')
    return _profile_loader

