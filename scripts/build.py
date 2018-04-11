#!/usr/bin/env python
"""Script to build code"""
import argparse
import os
import subprocess
from pathlib import Path

import hu_build.build_docker
import hu_build.build_package
from hu_build.build_docker import DockerImage

SCRIPT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR = SCRIPT_PATH.parent


class Error(Exception):
    """Base exception for this module"""
    pass


class PytestError(Error):
    """Pytest exception"""
    pass


def python_test(name, build_args, path, venv_location, ignore_dirs=None):
    """Does a Pytest build from a virtual environment"""
    venv_executable = str(venv_location / 'bin' / 'python')
    cmdline = [
        venv_executable, "-m", "pytest",
        str(path), "-m", "not integration_test",
        "--junitxml=TEST-pytest.{}.xml".format(name), "--timeout=70"
    ]
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
    if not build_args.no_test:
        hu_build.build_package.package_test(
            'entity_recognizer', src_path, timeout=70)
    if build_args.docker_build:
        tag_version = build_args.version
        docker_image = DockerImage(
            src_path,
            'api/entity_recognizer',
            image_tag=tag_version,
            registry='eu.gcr.io/hutoma-backend')
        hu_build.build_docker.build_single_image(
            "api-entity", docker_image, push=build_args.docker_push)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Python Common build command-line')
    PARSER.add_argument('--no-test', help='skip tests', action="store_true")
    PARSER.add_argument('--version', help='build version', default='latest')
    PARSER.add_argument(
        '--docker-build', help='Build docker', action="store_true")
    PARSER.add_argument(
        '--docker-push', help='Push docker images to GCR', action="store_true")
    BUILD_ARGS = PARSER.parse_args()
    main(BUILD_ARGS)
