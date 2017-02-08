import logging
import os
import pprint

from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.ffmpeg import FFmpegConvert
from ffmpeg import jinja_env
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver


class FfmpegAction:

    def __init__(self, conf: dict):
        self._conf = conf
        logging.info('Creating FFmpegConvert object...')
        self._ffmpeg_convert = FFmpegConvert(conf['ffmpeg_path'], conf['temp_dir'])

    def run(self, input_url: str, action_params: dict, out_rel_path: str=None):
        logging.info('Using FFprobe to collect input file parameters...')
        ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        input_params = ffprobe_info.exec(input_url, show_programs=False)
        logging.debug('Input parameters:\r\n{}'.format(pprint.pformat(input_params)))

        logging.info('Searching for video and audio streams...')
        v_streams = {}
        a_streams = {}
        for s in input_params['streams']:
            if s['codec_type'] == 'video':
                v_streams[s['index']] = s
            elif s['codec_type'] == 'audio':
                a_streams[s['index']] = s
        v_streams_count = len(v_streams)
        a_streams_count = len(a_streams)
        logging.info('Found {} video stream(s) and {} audio stream(s)'.format(v_streams_count, a_streams_count))
        logging.debug('Video stream index(es): {}, audio stream indexes: {}'.format(
            ', '.join([str(v) for v in v_streams.keys()]),
            ', '.join([str(a) for a in a_streams.keys()])))
        logging.info('Trying to determine field mode of all video streams...')
        interlacing_modes = FFprobeInterlacedProgressiveSolver(self._conf).solve(input_url, len(v_streams))
        for k, v in interlacing_modes.items():
            v_streams[k]['field_mode'] = v

        profile_template_name = action_params['profile']
        logging.info('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.info('Building profile template rendering context...')
        context = {
            'in_filename': os.path.splitext(os.path.split(input_url)[1])[0],
            'in_format': input_params['format'],
            'in_v_streams_count': v_streams_count,
            'in_v_streams': v_streams,
            'in_a_streams_count': a_streams_count,
            'in_a_streams': a_streams,
        }
        logging.debug('Rendering context:\r\n{}'.format(pprint.pformat(context)))
        profile_data = template.render(context)
        logging.info('Profile rendering complete')
        logging.debug('Rendered profile:\r\n{}'.format(profile_data))
