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
import time
import logging
import os.path
import readline
import sys
import getopt
from aligo import Aligo


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
            # print(f'{_f.file_id:<42s}{_f.type:<8s}{_f.name:<10s}')
            _type = _f.type.replace('folder', 'd').replace('file', '-')
            _size = _f.size if _f.size is not None else 0
            _name = _f.name

            # for auto-complete shell input
            self.file_names.append(_name)

            print(f'{_type:<3s}{_size:<8d}{_name:<10s}')

    def pwd_files(self):
        if self.PWD in ['/', '/Default']:
            file_id = 'root'
        else:
            file_id = self.get_path_id(self.PWD)

        try:
            time.sleep(3)
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

        # if self.path_is_file(source):
        #     file_id = self.get_file_by_path(source).file_id
        # elif self.path_is_dir(source):
        #     file_id = self.get_folder_by_path(source).file_id

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

    def rm(self, *path):
        for _path in path:
            # fixme cannot recognise path contains blank or "
            _path = os.path.join(self.PWD, _path)

            self.move_file_to_trash(file_id=self.get_path_id(_path))

    def mkdir(self):
        pass

    def touch(self):
        pass

    def interact_cli(self):
        files_pwd = self.pwd_files()

        self.file_names.extend(files_pwd)

        prompt = f'{self.user_name} # '
        while True:
            # files_pwd = self.pwd_files()

            def path_completer(text, state):
                names = []
                first_part = ' '.join(text.split()[0:-1])
                last_part = text.split()[-1]

                # for f in files_pwd:
                for f in self.file_names:
                    if f.startswith(last_part):
                        names.append(f)

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
                    _opt, *_target = _command.split()
                    self.rm(*_target)

                except IndexError:
                    pass

            else:
                print('command not supported.')


if __name__ == '__main__':
    ali_disk = AliDisk(mail_addr='beyan@beyan.me', secret='This is my secrets.', level=logging.WARN)

    options = sys.argv[1:]

    if not options:
        ali_disk.interact_cli()

    else:
        try:
            opts, args = getopt.getopt(options, '', [''])

            for opt, arg in opts:
                pass

        except getopt.GetoptError:
            pass



