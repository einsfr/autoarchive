import logging

from ffmpeg import create_ffmpeg_factory, create_ffprobe_factory, create_profile_loader
from ffmpeg.factory import FFmpegFactory, FFprobeFactory
from ffmpeg.profile_loader import ProfileLoader
from ffmpeg.profile_data_provider import JinjaProfileDataProvider
from ffmpeg.profile_data_parser import JsonProfileDataParser
from autoarchive import app

logging.debug('Initializing ffmpeg module...')
create_ffmpeg_factory(FFmpegFactory, ffmpeg_path=app.conf['ffmpeg_path'], temp_dir=app.conf['temp_dir'])
create_ffprobe_factory(FFprobeFactory, ffprobe_path=app.conf['ffprobe_path'])
create_profile_loader(ProfileLoader, data_provider=JinjaProfileDataProvider(), data_parser=JsonProfileDataParser())
logging.debug('Done')
