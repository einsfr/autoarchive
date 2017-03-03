import logging
import os


def build_file_list(input_path: str) -> tuple:
    logging.debug('Building file list...')
    dir_list = []
    file_count = 0
    for path, dirs, files in os.walk(input_path):
        if len(files):
            dir_list.append({'rel_in_dir': path[len(input_path) + 1:], 'files': files})
            file_count += len(files)
    logging.debug('Found {} files(s) in {} directory(ies)'.format(file_count, len(dir_list)))
    return dir_list, file_count
