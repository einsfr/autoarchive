import argparse
import json
import sys
import subprocess
from collections import deque
import os
import uuid
import shutil


def error(msg):
    sys.stderr.write('ERROR: {}'.format(msg))
    sys.exit(1)


def log(msg, verbosity):
    if verbosity >= 1:
        print(msg)


def info(msg, verbosity):
    if verbosity >= 2:
        print('INFO: {}'.format(msg))


def warning(msg):
    sys.stderr.write('WARNING: {}'.format(msg))


class ConversionException(Exception):
    pass


class Application:

    def __init__(self, base_dir, args):
        self.args = args
        self.verbosity = args.verbosity
        self.base_dir = base_dir
        self.command = args.command
        self.config_path = os.path.normpath(os.path.join(self.base_dir, 'config.json'))
        self.config = None
        self.ffmpeg_path = ''
        self.temp_dir = ''
        self.profiles_dir = os.path.normpath(os.path.join(self.base_dir, 'profiles'))
        self.profile_path = ''
        self.profile = None
        self.input_path = ''
        self.output_dir = ''

    def _read_config(self):
        self._info('Reading configuration file')
        try:
            with open(self.config_path) as c_file:
                self.config = self._check_config(json.load(c_file))
        except FileNotFoundError:
            error('Configuration file not found: "{}".'.format(self.config_path))
        except ValueError as e:
            error('Configuration file "{}" is not a valid JSON document: {}'.format(self.config_path, str(e)))
        self.ffmpeg_path = os.path.normpath(self.config['ffmpeg_path'])
        self.temp_dir = os.path.normpath(self.config['temp_dir'])

    def _read_profile(self):
        self._info('Checking profiles directory')
        if not os.path.isdir(self.profiles_dir):
            error('Profile directory "{}" not found.'.format(self.profiles_dir))
        self.profile_path = os.path.join(self.profiles_dir, '{}.json'.format(self.args.profile))
        self._info('Reading profile')
        try:
            with open(self.profile_path) as p_file:
                self.profile = self._check_profile(json.load(p_file))
        except FileNotFoundError:
            error('Profile "{}" not found.'.format(self.profile_path))
        except ValueError as e:
            error('Profile "{}" is not a valid JSON document: {}'.format(self.profile_path, str(e)))

    def _read_input_path(self):
        self.input_path = os.path.normpath(self.args.in_path)
        self._info('Checking input path')
        if not os.path.exists(self.input_path):
            error('Input path "{}" does not exist.'.format(self.input_path))

    def _read_output_dir(self):
        self.output_dir = os.path.normpath(self.args.out_path)
        self._info('Checking output path')
        if not os.path.isdir(self.output_dir):
            error('Output path "{}" is not an existing directory.')

    def exec(self):
        if self.command == 'run':
            self._cmd_run()

    def _cmd_run(self):
        self._read_config()
        self._read_profile()
        self._read_input_path()
        self._read_output_dir()
        if os.path.isfile(self.input_path):
            self._run_file()
        else:
            self._run_dir()

    def _info(self, msg):
        info(msg, self.verbosity)

    def _log(self, msg):
        log(msg, self.verbosity)

    def _check_config(self, config):
        self._info('Checking required configuration parameters')
        required_parameters = ['ffmpeg_path', 'temp_dir']
        for rp in required_parameters:
            if rp not in config:
                error('Required configuration parameter "{}" is missing.'.format(rp))

        if not os.path.isfile(os.path.normpath(config['ffmpeg_path'])):
            error('Path in configuration parameter ffmpeg_path "{}" is not a file.'.format(config['ffmpeg_path']))

        if not os.path.isdir(os.path.normpath(config['temp_dir'])):
            error('Path in configuration parameter temp_dir "{}" is not a directory.'.format(config['temp_dir']))

        return config

    def _check_profile(self, profile):
        self._info('Checking profile')
        if 'input' not in profile:
            error('Required profile section "input" is missing.')
        required_input_params = ['allowed_extensions']
        for rp in required_input_params:
            if rp not in profile['input']:
                error('Required input parameter "{}" is missing.'.format(rp))
        if type(profile['input']['allowed_extensions']) != list:
            error('Input parameter "allowed_extensions" must be an array.')

        if 'outputs' not in profile:
            error('Required profile section "outputs" is missing.')
        if type(profile['outputs']) != list:
            error('Profile section "outputs" must be an array.')
        if len(profile['outputs']) == 0:
            error('Profile must have at least one output.')
        required_output_params = ['parameters', 'extension']
        extensions = []
        for k, o in enumerate(profile['outputs']):
            if type(o) != dict:
                error('Output "{}" configuration is not an object.'.format(k))
            for rp in required_output_params:
                if rp not in o:
                    error('Required output "{}" parameter "{}" is missing.'.format(k, rp))
            if type(o['parameters']) != list:
                error('Output "{}" "parameters" must be an array.')
            extensions.append(str(o['extension']).lower())
        if len(set(extensions)) < len(extensions):
            error('All output extensions must be unique.')

        return profile

    def _run_file(self):
        self._log('Processing file "{}"'.format(self.input_path))
        self._info('Checking file extension')
        name, ext = os.path.splitext(os.path.split(self.input_path)[1])
        ext = ext.lower()
        allowed_exts = self.profile['input']['allowed_extensions']
        if ext not in allowed_exts:
            error('Wrong input file extension: "{}". Profile requires: {}.'.format(ext, allowed_exts))
        self._info('Building command')
        args = [self.ffmpeg_path, '-hide_banner', '-n', '-nostdin', '-i', self.input_path]
        tmp_paths = []
        output_mapping = {}
        tmp_name = uuid.uuid4()
        for o in self.profile['outputs']:
            args.extend(o['parameters'])
            tp = os.path.join(self.temp_dir, '{}{}'.format(tmp_name, o['extension']))
            op = os.path.join(self.output_dir, '{}{}'.format(name, o['extension']))
            if os.path.exists(op):
                error('Output file "{}" already exists.'.format(op))
            output_mapping[tp] = op
            tmp_paths.append(tp)
            args.append(tp)
        args_info = []
        for a in args:
            if a.find(' ') > 0:
                args_info.append('"{0}"'.format(a))
            else:
                args_info.append(a)
        self._info('Starting {}'.format(' '.join(args_info)))
        conv_log = deque(maxlen=5)
        conv_exception = None
        self._hook_pre_start()
        proc = subprocess.Popen(args, stderr=subprocess.PIPE, universal_newlines=True)
        self._hook_post_start()
        try:
            for line in proc.stderr:
                conv_log.append(line)
                if line.startswith('frame='):
                    p = line.find('fps=')
                    try:
                        frame = int(line[6:p].strip())
                    except ValueError as e:
                        raise ConversionException('Unable to determine conversion progress.') from e
                    self._progress_callback(frame)
        except ConversionException as e:
            proc.terminate()
            conv_exception = e
        except:
            proc.terminate()
            raise
        finally:
            proc.wait()
            return_code = proc.returncode
            if return_code != 0:
                self._error_callback(return_code, conv_log, conv_exception, tmp_paths)
            else:
                self._success_callback(output_mapping)

    def _run_dir(self):
        pass

    def _progress_callback(self, frame):
        self._info('Processed {} frames'.format(frame))
        self._hook_progress(frame)

    def _error_callback(self, return_code, conv_log, conv_exception, tmp_paths):
        self._info('Removing temporary files...')
        for tp in tmp_paths:
            if os.path.exists(tp):
                os.remove(tp)
        error(
            'ffmpeg process finished with exit code {}.\r\nLast output:\r\n{}\r\nRaised exception: {}'.format(
                return_code, '\r\n'.join(conv_log), conv_exception
            )
        )

    def _success_callback(self, output_mapping):
        self._info('ffmpeg process finished with exit code 0')
        self._info('Output mappings: {}'.format(output_mapping))
        self._hook_success()
        self._move_from_temp(output_mapping)

    def _move_from_temp(self, output_mapping):
        self._info('Moving files from temporary dir')
        self._hook_pre_move(output_mapping)
        for tp, op in output_mapping.items():
            if os.path.exists(op):
                warning('Output file "{}" already exists. Adding some random characters to file name.'.format(op))
                head, tail = os.path.split(op)
                name, ext = os.path.splitext(tail)
                op = os.path.join(head, '{}.{}{}'.format(name, uuid.uuid4(), ext))
            shutil.move(tp, op)
        self._hook_post_move(output_mapping)
        self._info('All done!')

    def _hook_pre_start(self):
        pass

    def _hook_post_start(self):
        pass

    def _hook_progress(self, frame):
        pass

    def _hook_success(self):
        pass

    def _hook_pre_move(self, output_mapping):
        pass

    def _hook_post_move(self, output_mapping):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbosity',
        help='verbosity level: 0 - silent (only stderr output), 1 - standard, 2 - verbose (output includes all '
             'INFO messages)',
        type=int,
        default=1
    )
    subparsers = parser.add_subparsers(dest='command', help='command')
    parser_run = subparsers.add_parser('run')
    parser_run.add_argument('in_path', help="path to input file or directory")
    parser_run.add_argument('out_path', help="path to output directory")
    parser_run.add_argument('profile', help="conversion profile's name")
    app = Application(os.path.dirname(os.path.realpath(__file__)), parser.parse_args())
    app.exec()
