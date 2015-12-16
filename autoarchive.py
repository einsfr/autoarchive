import argparse
import json
import sys
import subprocess
from collections import deque
import os
import uuid
import shutil
import datetime

VERSION = '1.0b'


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


class FfmpegException(Exception):
    pass


class RunExecException(Exception):
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
        self.simulate = False
        self.dir_depth = 0
        self.create_dir = False

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
        self.simulate = self.args.simulate
        self.dir_depth = self.args.dir_depth
        self.create_dir = self.args.create_dir
        if self.simulate:
            self._log('--- THIS IS A SIMULATION. NO CHANGES WILL BE MADE ---')
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
        allowed_exts = [e.lower() for e in self.profile['input']['allowed_extensions']]
        if ext not in allowed_exts:
            error('Wrong input file extension: "{}". Profile requires: {}.'.format(ext, allowed_exts))
        try:
            self._run_exec(self.input_path, self.output_dir)
        except RunExecException as e:
            error(str(e))

    def _run_dir(self):
        if self.create_dir:
            output_base_dir = os.path.join(self.output_dir, os.path.split(self.input_path)[1])
        else:
            output_base_dir = self.output_dir
        start_time = datetime.datetime.now()
        self._info('Building file list')
        file_list = self._build_file_list()
        dir_count = len(file_list)
        file_count = 0
        for f in file_list:
            file_count += len(f['files'])
        self._info('Found {} file(s) in {} directory(ies).'.format(file_count, dir_count))
        file_counter = 0
        errors_counter = 0
        for f in file_list:
            if self.dir_depth > 0:
                path = f['dir']
                path_list = []
                while True:
                    head, tail = os.path.split(path)
                    path = head
                    if tail:
                        path_list.append(tail)
                    if not head:
                        break
                if len(path_list) == 0:
                    output_dir = output_base_dir
                else:
                    if len(path_list) < self.dir_depth:
                        output_dir = os.path.join(output_base_dir, *path_list[::-1])
                    else:
                        output_dir = os.path.join(output_base_dir, *path_list[:-self.dir_depth - 1:-1])
                    if not self.simulate:
                        os.makedirs(output_dir, exist_ok=True)
            else:
                output_dir = output_base_dir
                if not self.simulate:
                    os.makedirs(output_dir, exist_ok=True)
            for file in f['files']:
                input_path = os.path.join(self.input_path, f['dir'], file)
                file_counter += 1
                self._log('Processing file {} of {}: "{}"'.format(file_counter, file_count, input_path))
                try:
                    self._run_exec(input_path, output_dir)
                except RunExecException as e:
                    errors_counter += 1
                    warning(str(e))
        if errors_counter:
            warning('Finished with {} error(s)'.format(errors_counter))
        else:
            self._log('Finished without errors')
        self._log('Elapsed time: {}'.format(datetime.datetime.now() - start_time))

    def _run_exec(self, input_path, output_dir):
        name = os.path.splitext(os.path.split(input_path)[1])[0]
        self._info('Building command')
        args = [self.ffmpeg_path, '-hide_banner', '-n', '-nostdin', '-loglevel', 'warning', '-stats', '-i', input_path]
        tmp_paths = []
        output_mapping = {}
        tmp_name = uuid.uuid4()
        for o in self.profile['outputs']:
            args.extend(o['parameters'])
            tp = os.path.join(self.temp_dir, '{}{}'.format(tmp_name, o['extension']))
            op = os.path.join(output_dir, '{}{}'.format(name, o['extension']))
            if os.path.exists(op):
                raise RunExecException('Output file "{}" already exists.'.format(op))
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
        if self.simulate:
            self._success_callback(output_mapping)
        else:
            conv_log = deque(maxlen=5)
            conv_exception = None
            self._hook_pre_start()
            proc = subprocess.Popen(args, stderr=subprocess.PIPE, universal_newlines=True)
            start_time = datetime.datetime.now()
            self._log('ffmpeg process started at {}'.format(start_time))
            self._hook_post_start()
            try:
                for line in proc.stderr:
                    conv_log.append(line)
                    if line.startswith('frame='):
                        p = line.find('fps=')
                        try:
                            frame = int(line[6:p].strip())
                        except ValueError as e:
                            raise FfmpegException('Unable to determine conversion progress.') from e
                        self._progress_callback(frame)
            except FfmpegException as e:
                proc.terminate()
                conv_exception = e
            except Exception as e:
                proc.terminate()
                error(str(e))
            finally:
                proc.wait()
                end_time = datetime.datetime.now()
                self._log('ffmpeg process finished. Elapsed time: {}'.format(end_time - start_time))
                return_code = proc.returncode
                if return_code != 0:
                    self._error_callback(return_code, conv_log, conv_exception, tmp_paths)
                else:
                    self._success_callback(output_mapping)

    def _build_file_list(self):
        file_list = []
        root_len = len(self.input_path)
        allowed_exts = [e.lower() for e in self.profile['input']['allowed_extensions']]
        for path, dirs, files in os.walk(self.input_path):
            files_allowed = [f for f in files if os.path.splitext(f)[1].lower() in allowed_exts]
            if len(files_allowed) > 0:
                file_list.append({'dir': path[root_len + 1:], 'files': files_allowed})
        return file_list

    def _progress_callback(self, frame):
        self._info('Processed {} frames'.format(frame))
        self._hook_progress(frame)

    def _error_callback(self, return_code, conv_log, conv_exception, tmp_paths):
        self._info('Removing temporary files')
        for tp in tmp_paths:
            if os.path.exists(tp):
                os.remove(tp)
        raise RunExecException(
            'Exit code {}.\r\nLast output:\r\n{}\r\nRaised exception: {}'.format(
                return_code, '\r\n'.join(conv_log), conv_exception
            )
        )

    def _success_callback(self, output_mapping):
        self._info('Output mappings: {}'.format(output_mapping))
        if not self.simulate:
            self._hook_success()
            self._move_from_temp(output_mapping)
        self._log('Done')

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
    parser_run.add_argument(
        '-dd', '--dirdepth',
        dest='dir_depth',
        help="directory structure depth in output folder",
        type=int,
        default=0
    )
    parser_run.add_argument(
        '-s', '--simulate',
        help="simulate run without using ffmpeg",
        action='store_true'
    )
    parser_run.add_argument(
        '-c', '--createdir',
        dest='create_dir',
        help="create input dir (if it's a dir) in output folder",
        action='store_true'
    )
    app = Application(os.path.dirname(os.path.realpath(__file__)), parser.parse_args())
    app.exec()
