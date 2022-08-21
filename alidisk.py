#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2022 by ZHANG ZHIJIE.
# All rights reserved.

# Created Time: 8/20/22 09:24
# Author: ZHANG ZHIJIE
# Email: norvyn@norvyn.com
# Git: @n0rvyn
# File Name: alidisk.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
import glob
import signal
import time
import logging
import os.path
import readline
import sys
import getopt
from aligo import Aligo
from typing import Optional
from typing_extensions import Literal

CheckNameMode = Optional[
    Literal[
        'auto_rename',  # automatically rename the file if source & target has the same name
        'refuse',  # refuse upload
        'overwrite',  # overwrite without prompt
    ]
]


class AliDisk(Aligo):
    def __init__(self, mail_addr=None, secret=None, level=logging.INFO):
        self.PWD = '/'
        self.file_names = []

        if mail_addr is not None:
            Aligo.__init__(self, email=(mail_addr, secret), level=level)
        else:
            Aligo.__init__(self, level=level)

    def ls(self, path=None):
        path = path if path is not None else self.PWD

        # pwd_path_id = self.get_folder_by_path(path=path).file_id
        if self.PWD in ['/', '/Default']:
            pwd_path_id = 'root'
        else:
            pwd_path_id = self.get_path_id(path)

        files = self.get_file_list(parent_file_id=pwd_path_id)
        print(f'total {len(files)}')

        for _f in files:
            try:

                _type = _f.type.replace('folder', 'd').replace('file', '-')
                _size = _f.size if _f.size is not None else 0
                _name = _f.name

                # for auto-complete shell input
                self.file_names.append(_name)

                print(f'{_type:<3s}{_size:<8d}{_name:<10s}')

            except AttributeError:
                pass

    def pwd_files(self):
        if self.PWD in ['/', '/Default']:
            file_id = 'root'
        else:
            file_id = self.get_path_id(self.PWD)

        try:
            time.sleep(5)
            return [file.name for file in self.get_file_list(parent_file_id=file_id)]
        except AttributeError:
            return []

    def pwd(self):
        print(self.PWD)

    def cd(self, path):
        folder = self.get_folder_by_path(path)
        # todo add support for '.' and '..'

        if folder is None:
            return self.PWD

        folder_id = folder.file_id
        path_response = self.get_path(file_id=folder_id)  # returns all folders with the same name

        for _path in path_response.items:
            _name = _path.name
            _id = _path.file_id

            _name = '/' if _name == 'Default' else _name

            if _id == folder_id:
                self.PWD = os.path.join(self.PWD, _name)

        return self.PWD

    def path_is_file(self, path):
        try:
            _type = self.get_file_by_path(path=path).type

            if _type == 'file':
                return True

        except AttributeError:
            pass

        return False

    def path_is_dir(self, path):
        try:
            _type = self.get_folder_by_path(path=path).type

            if _type == 'folder':
                return True

        except AttributeError:
            pass

        return False

    def get_path_id(self, path):
        if self.path_is_file(path):
            return self.get_file_by_path(path).file_id
        elif self.path_is_dir(path):
            return self.get_folder_by_path(path).file_id

    def mv(self, source, target, copy=False):
        if self.path_is_file(target):
            prompt = input('Target name exist, overwrite or not: [No/yes]')

            if prompt.upper() in ['Y', 'YES']:
                pass

            else:
                print('Receive overwrite=False, nothing moved.')
                return False

        elif not self.path_is_dir(target):
            print('target path not exist, nothing moved.')
            return False

        source = os.path.join(self.PWD, source)
        target = os.path.join(self.PWD, target)

        move_to_path = move_to_name = None
        file_id = self.get_path_id(source)

        if self.path_is_dir(target):
            move_to_path = target
        elif self.path_is_file(target):
            move_to_path = os.path.dirname(target)
            move_to_name = os.path.basename(target)

        move_to_path_id = self.get_folder_by_path(move_to_path).file_id

        if copy:
            return self.copy_file(file_id=file_id, to_parent_file_id=move_to_path_id, new_name=move_to_name)
        else:
            return self.move_file(file_id=file_id, to_parent_file_id=move_to_path_id, new_name=move_to_name)

    def rm(self, path):
        path_delete = []

        if path.endswith('*'):
            path_prefix = path.rstrip('*')
            files_pwd = self.pwd_files()

            for file_name in files_pwd:
                if file_name.startswith(path_prefix):
                    path_delete.append(os.path.join(self.PWD, file_name))

        else:
            path_delete = [os.path.join(self.PWD, path)]

        # todo add support for delete files with regular expression
        for path in path_delete:
            self.move_file_to_trash(file_id=self.get_path_id(path))

    def mkdir(self, path):
        full_path = os.path.join(self.PWD, path)

        name = os.path.basename(full_path)
        parent_path = os.path.dirname(full_path)

        parent_path_id = self.get_path_id(parent_path)
        return self.create_folder(name=name, parent_file_id=parent_path_id, check_name_mode='overwrite')

    def upload(self, source, target=None, check_name_mode: CheckNameMode = None):
        target = target if target is not None else self.PWD  # upload to current working dir, if nothing specified.
        target = os.path.join(self.PWD, target)

        if os.path.isdir(source):
            target_parent_path = os.path.dirname(target)
            target_id = self.get_path_id(target_parent_path)

            try:
                self.upload_folder(folder_path=source, parent_file_id=target_id,
                                   check_name_mode='overwrite', folder_check_name_mode=check_name_mode)
            except AttributeError:
                print('upload failed')

        if os.path.isfile(source):
            if self.path_is_dir(target):
                parent_id = self.get_path_id(target)
                name = None

            else:
                parent_id = self.get_path_id(os.path.basename(target))
                name = os.path.basename(target)

            try:
                self.upload_file(source, name=name, parent_file_id=parent_id, check_name_mode=check_name_mode)
            except AttributeError:
                print('upload failed')

    def upload_many(self, *source, target=None, check_name_mode: CheckNameMode = None):
        dirs_upload = []
        files_upload = []
        target = '/' if target is None else target

        for s in source:
            if os.path.isfile(s):
                files_upload.append(s)

            if os.path.isdir(s):
                dirs_upload.append(s)

        for d in dirs_upload:
            print(f'upload directory {d}')
            self.upload_folder(folder_path=d,
                               parent_file_id=self.get_path_id(target),
                               check_name_mode=check_name_mode)

        print(f'upload files {" ".join(files_upload)}')
        self.upload_files(file_paths=files_upload,
                                 parent_file_id=self.get_path_id(target),
                                 check_name_mode=check_name_mode)

    def download(self, source, target=None):
        for _dir in ['download', 'downloads', 'Downloads', 'Download']:
            _full_path = os.path.join(os.environ['HOME'], _dir)
            if os.path.exists(_full_path) and target is None:
                target = _full_path

        target = target if target is not None else '.'

        source = os.path.join(self.PWD, source)
        source_id = self.get_path_id(source)

        if self.path_is_file(source):
            return self.download_file(file_id=source_id, local_folder=target)

        elif self.path_is_dir(source):
            return self.download_folder(folder_file_id=source_id, local_folder=target)

    def download_many(self, *source, target=None):
        """
        For now, only support multiple files under the same directory.

        Args:
            *source:
            target:

        Returns:

        """
        print('sleep 5 sec for account audit then start list files')
        time.sleep(5)

        self.cd(os.path.dirname(source[0]))
        files_pwd = self.pwd_files()

        for source_path in source:
            if source_path.endswith('*'):
                _name_prefix = os.path.basename(source_path.rstrip('*'))
                for file in files_pwd:
                    if file.startswith(_name_prefix):
                        time.sleep(1)
                        print('download file: ', file)
                        self.download(source=file, target=target)
            else:
                print('download file: ', source_path)
                self.download(source=source_path, target=target)

    def usage(self):
        pass

    def interact_cli(self, oneshot=False):
        files_pwd = self.pwd_files()
        self.file_names.extend(files_pwd)

        def signal_handler(signum, frame):
            print('\nCTRL-C signal detected, exit with [q | quit | exit].')

        signal.signal(signal.SIGINT, handler=signal_handler)

        prompt = f'{self.user_name} # '

        while True:
            # files_pwd = self.pwd_files()  # avoid every loop list files in the driver, which cause security issues.
            def path_completer(text, state):
                names = []

                if '"' in text:
                    first_part = '"'.join(text.split('"')[0:-1])
                    last_part = text.split('"')[-1]

                else:
                    first_part = ' '.join(text.split()[0:-1])
                    last_part = text.split()[-1]

                # for f in files_pwd:
                for f in self.file_names:
                    if f.startswith(last_part):
                        names.append(f)

                if '"' in text:
                    return f'{first_part}"{names[state]}"'  # auto complete line contains ' '(blank)
                else:
                    return f'{first_part} {names[state]}'

            readline.set_completer_delims('\t')

            readline.parse_and_bind('tab: complete')
            readline.set_completer(path_completer)
            _command = input(prompt)
            readline.add_history(_command)

            if _command in ['quit', 'q', 'exit']:
                break

            elif _command == '':
                pass

            elif _command == 'logout':
                self.logout()
                exit(0)

            elif _command.startswith('ls'):
                self.ls()

            elif _command == 'pwd':
                self.pwd()

            elif _command.startswith('cd'):
                _path = ' '.join(_command.split()[1:])
                self.cd(path=_path)

            elif _command.startswith('mv'):
                try:
                    _source = _command.split()[1]
                    _target = _command.split()[2]

                    self.mv(_source, _target)

                except IndexError:
                    pass

            elif _command.startswith('cp'):
                try:
                    _source = _command.split()[1]
                    _target = _command.split()[2]

                    self.mv(_source, _target, copy=True)

                except IndexError:
                    pass

            elif _command.startswith('rm'):
                try:
                    # _target = _command.split()[-1]  # only support removing 1 file onetime this moment
                    #
                    _target = _command.lstrip('rm ').strip('"')
                    self.rm(_target)

                except IndexError:
                    pass

            elif _command.startswith('mkdir'):
                pass

            elif _command.startswith('upload'):  # todo add sth
                pass

            elif _command.startswith('download'):
                pass

            else:
                print('command not supported.')


if __name__ == '__main__':
    ali_disk = AliDisk(mail_addr='beyan@beyan.me', secret='This is my secrets.', level=logging.WARN)

    options = sys.argv[1:]
    mode: CheckNameMode = 'refuse'

    if not options:
        ali_disk.interact_cli()

    else:
        try:
            opts, args = getopt.getopt(options, 'udoar', ['upload',
                                                          'download',
                                                          'overwrite',
                                                          'auto-rename',
                                                          'rename',
                                                          'refuse'])

            for opt, arg in opts:
                if opt in ['--overwrite', '-o']:
                    mode: CheckNameMode = 'overwrite'
                if opt in ['--auto-rename', '-a']:
                    mode: CheckNameMode = 'auto_rename'
                if opt == ['--refuse', '-r']:
                    mode: CheckNameMode = 'refuse'

            for opt, arg in opts:
                if opt in ['-u', '--upload']:
                    _args_index = sys.argv.index(opt) + 1
                    _args = sys.argv[_args_index:]  # read all args behind '-u' or '--upload'

                    # if not os.path.isdir(_args[-1]) and not os.path.isfile(_args[-1]):
                    if not os.path.exists(_args[-1]):
                        _source_path = _args[0:-1]
                        _target_path = _args[-1]
                    else:
                        _source_path = _args
                        _target_path = '/'

                    ali_disk.upload_many(*_source_path, target=_target_path, check_name_mode=mode)

                elif opt in ['-d', '--download']:
                    _args_index = sys.argv.index(opt) + 1
                    _args = sys.argv[_args_index:]

                    if os.path.exists(_args[-1]):
                        _source_path = _args[0:-1]
                        _target_path = _args[-1]
                    else:
                        _source_path = _args
                        _target_path = None

                    ali_disk.download_many(*_source_path, target=_target_path)

        except getopt.GetoptError as e:
            print(e)

        except IndexError:
            pass
