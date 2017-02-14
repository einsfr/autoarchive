import logging
import os
import pprint
import json
import jsonschema

from dispatcher import ActionRunException
from action import OutDirCreatingAction
from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.ffmpeg import FFmpegConvertCommand
from ffmpeg import jinja_env
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver
from ffmpeg import exceptions as ffmpeg_exceptions


class FfmpegConvertAction(OutDirCreatingAction):

    PROFILE_SCHEMA = {
        'title': 'Profile',
        'type': 'object',
        'properties': {
            'inputs': {
                'title': 'Profile inputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile input',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile input\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile input\'s parameter',
                                'type': 'string'
                            }
                        }
                    },
                    'required': ['parameters', ]
                },
                'minItems': 1
            },
            'outputs': {
                'title': 'Profile outputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile output',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile output\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile output\'s parameter',
                                'type': 'string'
                            }
                        },
                        'filename': {
                            'title': 'Profile output\'s filename',
                            'type': 'string'
                        }
                    },
                    'required': ['parameters', 'filename', ]
                },
                'minItems': 1
            }
        },
        'required': ['inputs', 'outputs']
    }

    def __init__(self, conf: dict, simulate: bool):
        super().__init__(conf, simulate)
        logging.debug('Creating FFmpegConvertCommand object...')
        self._ffmpeg_convert = FFmpegConvertCommand(conf['ffmpeg_path'], conf['temp_dir'], simulate)
        logging.debug('Creating FFprobeInfoCommand object...')
        self._ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        logging.debug('Creating FFprobeInterlacedProgressiveSolver object...')
        self._int_prog_solver = FFprobeInterlacedProgressiveSolver(self._conf)

    @classmethod
    def _validate_profile(cls, profile_dict: dict) -> None:
        logging.debug('Validating profile...')
        jsonschema.validate(profile_dict, cls.PROFILE_SCHEMA)

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        super().run(input_url, action_params, out_dir_path)
        logging.debug('Using FFprobe to collect input file parameters...')
        input_params = self._ffprobe_info.exec(input_url, show_programs=False)
        logging.debug('Input parameters:\r\n{}'.format(pprint.pformat(input_params)))

        logging.debug('Searching for video and audio streams...')
        v_streams = {}
        a_streams = {}
        for s in input_params['streams']:
            if s['codec_type'] == 'video':
                v_streams[s['index']] = s
            elif s['codec_type'] == 'audio':
                a_streams[s['index']] = s
        v_streams_count = len(v_streams)
        a_streams_count = len(a_streams)
        logging.debug('Found {} video stream(s) and {} audio stream(s)'.format(v_streams_count, a_streams_count))
        logging.debug('Video stream index(es): {}, audio stream indexes: {}'.format(
            ', '.join([str(v) for v in v_streams.keys()]),
            ', '.join([str(a) for a in a_streams.keys()])))
        logging.debug('Trying to determine field mode of all video streams...')
        interlacing_modes = self._int_prog_solver.solve(input_url, len(v_streams))
        for k, v in interlacing_modes.items():
            v_streams[k]['field_mode'] = v

        profile_template_name = action_params['profile']
        logging.debug('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.debug('Building profile template rendering context...')
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
        logging.debug('Rendered profile:\r\n{}'.format(profile_data))
        logging.debug('Profile rendering complete - loading...')
        try:
            profile_dict = json.loads(profile_data)
        except ValueError as e:
            raise ValueError('Profile {} is not a valid JSON document: {}'.format(profile_template_name, str(e)))
        self._validate_profile(profile_dict)
        logging.debug('Starting FFmpeg conversion...')
        try:
            self._ffmpeg_convert.exec(
                [(profile_dict['inputs'][0]['parameters'], input_url)],
                [(o['parameters'], os.path.join(out_dir_path, o['filename'])) for o in profile_dict['outputs']]
            )
        except (ffmpeg_exceptions.FFmpegInputNotFoundException, ffmpeg_exceptions.FFmpegOutputAlreadyExistsException,
                ffmpeg_exceptions.FFmpegProcessException) as e:
            raise ActionRunException from e
