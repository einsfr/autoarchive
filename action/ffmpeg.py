import logging
import os

from ffmpeg.ffprobe import FFprobeInfoCommand, FFprobeFrameCommand
from ffmpeg import jinja_env


class FfmpegAction:

    INTERLACING_DETERMINATION_FRAME_COUNT = 100

    def __init__(self, conf: dict):
        self._conf = conf

    def run(self, input_url: str, action_params: dict, out_rel_path: str=None):
        logging.info('Using FFprobe to collect input file parameters...')
        ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        input_params = ffprobe_info.exec(input_url, show_programs=False)
        logging.debug('Input parameters: {}'.format(input_params))

        logging.info('Searching for video and audio streams...')
        v_streams = {}
        a_streams = {}
        for s in input_params['streams']:
            if s['codec_type'] == 'video':
                v_streams[s['index']] = s
            elif s['codec_type'] == 'audio':
                a_streams[s['index']] = s
        logging.info('Found {} video stream(s) and {} audio stream(s)'.format(len(v_streams), len(a_streams)))
        logging.debug('Video stream index(es): {}, audio stream indexes: {}'.format(
            ', '.join([str(v) for v in v_streams.keys()]),
            ', '.join([str(a) for a in a_streams.keys()])))

        logging.info('Decoding some frames to determine interlacing mode...')
        ffprobe_frame = FFprobeFrameCommand(self._conf['ffprobe_path'])
        for n, vs in enumerate(v_streams.values()):
            v_frame_list = ffprobe_frame.exec(
                input_url,
                'v:{}'.format(n),
                '%+#{}'.format(self.INTERLACING_DETERMINATION_FRAME_COUNT)
            )['frames']
            interlaced = None
            tff = None

        profile_template_name = action_params['profile']
        logging.info('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.info('Building profile template rendering context...')
        context = {
            'in_filename': os.path.splitext(os.path.split(input_url)[1])[0],
            'in_format': input_params['format'],
            'in_v_streams': v_streams,
            'in_a_streams': a_streams,
        }
        logging.debug('Rendering context: {}'.format(context))
        profile_data = template.render(context)
        logging.info('Profile rendering complete')
        logging.debug('Rendered profile: {}'.format(profile_data))
