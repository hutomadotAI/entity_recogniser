#!/usr/bin/env python
"""Script to build code"""
import datetime
import argparse
import os
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR = SCRIPT_PATH.parent

class Error(Exception):
    """Base exception for this module"""
    pass

class PytestError(Error):
    """Pytest exception"""
    pass

def initialize_venv(venv_script):
    """Initialize the venv"""
    cmdline = ["bash", str(venv_script)]
    result = subprocess.run(cmdline)
    if result.returncode != 0:
        raise PytestError

def python_test(name, build_args, path, venv_location, ignore_dirs=None):
    """Does a Pytest build from a virtual environment"""
    venv_executable = str(venv_location / 'bin' / 'python')
    cmdline = [venv_executable, "-m", "pytest", str(path), "-m", "not integration_test",
               "--junitxml=TEST-pytest.{}.xml".format(name)]
    if ignore_dirs is not None:
        cmdline.append('--ignore={}'.format(ignore_dirs))

    if build_args.no_test:
        return
    result = subprocess.run(cmdline, cwd=str(path))
    if result.returncode != 0:
        raise PytestError


def main(build_args):
    """Main function"""
    src_path = ROOT_DIR / 'src'
    initialize_venv(ROOT_DIR/'scripts'/'setup_python.sh')
    python_test('entity_recognizer',
                build_args,
                src_path,
                ROOT_DIR/'venv'/'entity_unix',
                ignore_dirs='vendor')

    python_test('python_common',
                build_args,
                src_path/'vendor'/'common'/'src',
                ROOT_DIR/'venv'/'entity_unix')

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Python Common build command-line')
    PARSER.add_argument('--no-test', help='skip tests', action="store_true")
    BUILD_ARGS = PARSER.parse_args()
    main(BUILD_ARGS)
