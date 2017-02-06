import logging
import os

from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg import jinja_env


class FfmpegAction:

    def __init__(self, conf: dict):
        self._conf = conf

    def run(self, input_url: str, action_params: dict, out_rel_path: str=None):
        logging.info('Using FFprobe to fetch input file parameters...')
        ffprobe = FFprobeInfoCommand(self._conf['ffprobe_path'])
        input_params = ffprobe.exec(input_url, show_programs=False)
        logging.debug('Input parameters: {}'.format(input_params))
        profile_template_name = action_params['profile']
        logging.info('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.info('Building profile template rendering context...')
        context = {
            'input_filename': os.path.splitext(os.path.split(input_url)[1])[0],
            'input_format': input_params['format'],
            'input_streams': input_params['streams'],
        }
        logging.debug('Rendering context: {}'.format(context))
        profile_data = template.render(context)
        logging.info('Profile rendering complete')
        logging.debug('Rendered profile: {}'.format(profile_data))
