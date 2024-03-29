#!/usr/bin/env python
"""Script to build code"""
import argparse
import os
from pathlib import Path
import subprocess

import hu_build.build_docker
from hu_build.build_docker import DockerImage

SCRIPT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR = SCRIPT_PATH.parent


def main(build_args):
    """Main function"""
    src_path = ROOT_DIR / 'src'
    tag_version = build_args.version
    docker_image = DockerImage(
        src_path,
        'api/entity_recognizer',
        image_tag=tag_version,
        registry='eu.gcr.io/hutoma-backend')
    hu_build.build_docker.build_single_image(
        "api-entity", docker_image, push=build_args.docker_push)
    image_name = docker_image.full_image_tag()
    print("*** Building extracting results from images using container")
    result = subprocess.run(["docker", "create", image_name],
                            stdout=subprocess.PIPE,
                            encoding="utf8",
                            check=True)
    container_id = result.stdout.strip()
    subprocess.run([
        "docker", "cp", "{}:/tmp/tests.xml".format(container_id),
        "TESTS-emb.xml"
    ])
    print("*** Cleaning up")
    subprocess.run(["docker", "rm", "-v", "{}".format(container_id)])


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Entity-recognizer build command-line')
    PARSER.add_argument('--version', help='build version', default='latest')
    PARSER.add_argument(
        '--docker-build', help='Build docker', action="store_true")
    PARSER.add_argument(
        '--docker-push', help='Push docker images to GCR', action="store_true")
    BUILD_ARGS = PARSER.parse_args()
    main(BUILD_ARGS)
