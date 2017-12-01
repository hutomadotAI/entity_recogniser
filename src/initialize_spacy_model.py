#!/usr/bin/env python
"""Script to download models"""
import pip
import spacy

def load_model(model, version):
    # dive into PIP depths to get the info about the package we need
    # It's quicker to check in PIP than load it in Spacy
    dists_expression = pip.commands.show.search_packages_info([model])
    dists = list(dists_expression)
    if len(dists) < 1:
        return (False, None)
    dist = dists[0]
    found_version = dist['version']
    return(version == found_version, found_version)

def download_model(model, version):
    # Borrow from implementation of spacy's download command
    # But extend it so we can actually tell if it FAILED
    download_url = spacy.about.__download_url__ + \
        "/{m}-{v}/{m}-{v}.tar.gz".format(
            m=model, v=version)
    return_code = pip.main(['install', '--no-cache-dir', download_url])
    if return_code:
        print("Download failed")
        sys.exit(return_code)

if __name__ == "__main__":
    print("*** Initialize Spacy Model script")
    LANGUAGES = [
        ('en_core_web_sm', '2.0.0'),
        ('en_core_web_md', '2.0.0'),
        ('fr_core_news_sm', '2.0.0'),
        ('it_core_news_sm', '2.0.0'),
        ('nl_core_news_sm', '2.0.0')
    ]

    for model, version in LANGUAGES:
        download_model_required = True
        print("***********************************************************")
        print("*** Checking if {}:{} is available...".format(model, version))
        version_matches, found_version = load_model(model, version)
        if not version_matches:
            print("*** Model {}:{} not present, found {}".format(
                model, version, found_version))
        else:
            print("*** {}:{} found".format(model, version))
            download_model_required = False
        if download_model_required:
            download_model(model, version)
 