#!/usr/bin/env python
"""Script to build code"""
import os
import pip
import urllib
import wget
from pathlib import Path

if __name__ == "__main__":
    print("*** Initialize Spacy Model script")
    script_path = Path(os.path.dirname(os.path.realpath(__file__)))
    root_dir = script_path.parent

    # use a cache directory outside of the repository so that build servers 
    # don't need to keep downloading the large model file everytime.
    cache_dir = Path(os.path.expanduser('~/.cache/hu_build_cache/entity_recog'))
    src_dir = root_dir/'src'/'hu_entity'

    spacy_model_definition_file = src_dir/'spacy_model.txt'
    print("Loading model file definition from '{}'".format(spacy_model_definition_file))
    with spacy_model_definition_file.open() as fp:
        spacy_url_text = fp.read().strip()

    spacy_url_parsed = urllib.parse.urlparse(spacy_url_text)
    spacy_model_path = Path(spacy_url_parsed.path)
    spacy_model_filename = spacy_model_path.name
    cached_file = cache_dir/spacy_model_filename
    print("Spacy model is from URL:'{}', it will be cached at'{}'".format(spacy_url_text, cached_file))
    if not cached_file.exists():
        print("Downloading spacy model...")
        cache_dir.mkdir(exist_ok=True, parents=True)
        wget.download(spacy_url_text, str(cached_file))

    # The model file is PIP installed which will extract and wire it in as a Python module
    # you can import.
    # e.g.: import en_core_web_md
    print("PIP installing the spacy model...")
    pip.main(['install', str(cached_file)])
    print("*** End of Initialize Spacy Model script")
