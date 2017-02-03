import json
import subprocess
from collections import deque
import uuid
import shutil
import datetime
import os

from exceptions import FfmpegException, RunExecException


class OldApplication:

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
            error('Output path "{}" is not an existing directory.'.format(self.output_dir))

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
                error('Output "{}" "parameters" must be an array.'.format(k))
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

    def _build_file_list(self):
        file_list = []
        root_len = len(self.input_path)
        allowed_exts = [e.lower() for e in self.profile['input']['allowed_extensions']]
        for path, dirs, files in os.walk(self.input_path):
            files_allowed = [f for f in files if os.path.splitext(f)[1].lower() in allowed_exts]
            if len(files_allowed) > 0:
                file_list.append({'dir': path[root_len + 1:], 'files': files_allowed})
        return file_list
