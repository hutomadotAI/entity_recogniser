import pytest
from hu_entity.entity_finder import EntityFinder


def test_entity_finder_basic():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a Carrot cake")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_no_entities():
    finder = EntityFinder()
    values = {}
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a Carrot cake")
    assert(len(found_matches) == 0)


def test_entity_finder_no_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a cake")
    assert(len(found_matches) == 0)


def test_entity_finder_multiple_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a Carrot cake and then more carrot cake")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_duplicate_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a chocolate cake and a chocolate biscuit")
    assert(len(found_matches["chocolate"]) == 2)
    assert("CakeType" in found_matches["chocolate"])
    assert("Biscuit" in found_matches["chocolate"])


def test_entity_finder_multiple_value_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a Carrot cake and then a beer to drink")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])
    assert(len(found_matches["beer"]) == 1)
    assert("Drinks" in found_matches["beer"])


def test_entity_finder_case_insensitive():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a carrot cake")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_ignore_punctuation():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want a cake, maybe carrot?")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_multi_word_values():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.replace_entity_values("I want some red wine and a cake")
    assert(len(found_matches["red wine"]) == 1)
    assert("Drinks" in found_matches["red wine"])


def test_entity_finder_split_message():
    finder = EntityFinder()
    words = finder.split_message("This is short")
    assert(len(words) == 6)


@pytest.fixture()
def setup_data():
    values = {"CakeSize": ["Large", "Medium", "Tiny"],
              "CakeType": ["Carrot", "Chocolate", "Coffee", "Sponge"],
              "Drinks": ["Coffee", "Beer", "Red Wine", "White Wine"],
              "Biscuit": ["Rich Tea", "Digestive", "Chocolate"]}
    return values
