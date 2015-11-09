# coding: utf-8
'''
doit script for building the tools.

Run `doit` to create runnable scripts for all platforms.

See http://pydoit.org/ for details.

'''
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import datetime
import os
import shutil
import stat
import subprocess
import zipfile


DOIT_CONFIG = dict(default_tasks=['build'])

def task_git_clean():
    return dict(actions=[git_clean])


def task_test():
    return dict(
        actions=['''in-virtualenv -r test_requirements.txt python -m unittest discover -p '*test*.py' '''])


def task_zip():
    return dict(
        file_dep=subprocess.check_output(['git', 'ls-files']).splitlines(),
        actions=[make_zip],
        targets=['sources.zip'],
        clean=True)


def task_build():
    def windows(name):
        return '{}.cmd'.format(name)
    # windows = '{}.cmd'.format
    def unix(name):
        return name

    name_to_taxids = 'name-to-taxids-{}'.format(timestamp())
    build_index = 'build-index-{}'.format(timestamp())

    return dict(
        file_dep=['sources.zip'],
        actions=[
            (make_zipapp, [unix(    name_to_taxids), UNIX_PREFIX,    'firm_name_search.name_to_taxid']),
            (make_zipapp, [unix(    build_index),    UNIX_PREFIX,    'firm_name_search.build_index']),
            (make_zipapp, [windows( name_to_taxids), WINDOWS_PREFIX, 'firm_name_search.name_to_taxid']),
            (make_zipapp, [windows( build_index),    WINDOWS_PREFIX, 'firm_name_search.build_index'])],
        targets=[
            unix(name_to_taxids), windows(name_to_taxids),
            unix(build_index), windows(build_index)],
        clean=True)


###
# helpers, implementation

def run(cmd, *args, **kwargs):
    print(cmd, args, kwargs)
    subprocess.check_call(cmd.split(), *args, **kwargs)


def git_clean():
    run('git clean -X -f')


def make_zip():
    run('pip install . -t _build')
    # print(get_sources('_build').readlines())
    sources = subprocess.Popen(
        ['find',  '-name' , '*.py'], cwd='_build', stdout=subprocess.PIPE
    ).stdout
    run('zip -@q ../sources.zip', cwd='_build', stdin=sources)
    shutil.rmtree('_build', ignore_errors=True)


def timestamp():
    return datetime.date.today().strftime('%Y%m%d')


def make_executable(file):
    st = os.stat(file)
    os.chmod(file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


UNIX_PREFIX = b'#!/usr/bin/env python\n'

WINDOWS_PREFIX = b'\r\n'.join((
    b'@echo off',
    b'python.exe "%~f0" %*',
    b'exit /b %errorlevel%',
    b''))

MAIN_PY = '''\
from {module_path} import {main_function}
{main_function}()
'''


def make_zipapp(app_file, os_prefix, module_path, main_function='main'):
    shutil.copy('sources.zip', app_file)
    with zipfile.ZipFile(app_file, mode='a') as z:
        z.writestr(
            '__main__.py',
            MAIN_PY.format(
                module_path=module_path,
                main_function=main_function))
    with open(app_file, 'r+b') as f:
        app_zip = f.read()
        # rewrite with os_prefix
        f.seek(0)
        f.truncate()
        f.write(os_prefix)
        f.write(app_zip)
    make_executable(app_file)
