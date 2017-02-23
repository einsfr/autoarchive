import os

from args_parser import args_parser
import application
from ffmpeg import factory, profile_loader
from ffmpeg.profile_data_provider import JinjaProfileDataProvider
from ffmpeg.profile_data_parser import JsonProfileDataParser


if __name__ == '__main__':
    base_dir = os.path.dirname(__file__)
    app = application.Application(base_dir, args_parser.parse_args())
    application.app = app
    factory.ffmpeg_factory = factory.FFmpegFactory(app.conf['ffmpeg_path'], app.conf['temp_dir'])
    factory.ffprobe_factory = factory.FFprobeFactory(app.conf['ffprobe_path'])
    profile_loader.profile_loader = profile_loader.ProfileLoader(JinjaProfileDataProvider(),
                                                                 JsonProfileDataParser())
    app.exec()
