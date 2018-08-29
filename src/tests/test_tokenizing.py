import pytest

import hu_entity.spacy_wrapper


@pytest.fixture(scope="module")
def spacy_wrapper():
    """EntityRecognizerServer takes ages to initialize, so define a single EntityRecognizerServer
    which will be reused in every test"""
    server = hu_entity.spacy_wrapper.SpacyWrapper(minimal_ers_mode=True)
    server.initialize()
    return server


def test_tokenize_1(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "hi", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 1
    assert result[0] == "hi"


def test_tokenize_remove_person(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "Fred Bloggs rules OK", True,
        hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 2
    assert result[0] == "rule"
    assert result[1] == "ok"


def test_tokenize_anonymise_person_if_otherwise_empty(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "Fred Bloggs", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 1
    assert result[0] == "person"


def test_tokenize_remove_number(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "set alarm 12345", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 2
    assert result[0] == "set"
    assert result[1] == "alarm"


def test_anonymise_number_if_otherwise_empty(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "12345", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 1
    assert result[0] == "num"


def test_anonymise_floating_point_1(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "123.45", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 1
    assert result[0] == "num"


def test_anonymise_floating_point_2_not_replaced(spacy_wrapper):
    result = spacy_wrapper.tokenize(
        "1,234.50", True, hu_entity.spacy_wrapper.StopWordSize.DEFAULT)
    assert len(result) == 1
    assert result[0] == "1,234.50"
