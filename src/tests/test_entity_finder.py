import pytest
from hu_entity.entity_finder import EntityFinder


def test_entity_finder_basic():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a Carrot cake")
    assert(found_text == "I want a @CakeType cake")
    assert(len(found_values["CakeType"]) == 1)
    assert(next(iter(found_values["CakeType"])) == "carrot")


def test_entity_finder_no_entities():
    finder = EntityFinder()
    values = {}
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a Carrot cake")
    assert(found_text == "I want a Carrot cake")
    assert(len(found_values) == 0)


def test_entity_finder_no_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a cake")
    assert(found_text == "I want a cake")
    assert(len(found_values) == 0)


def test_entity_finder_multiple_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a Carrot cake and then more carrot cake")
    assert(found_text == "I want a @CakeType cake and then more @CakeType cake")
    assert(len(found_values["CakeType"]) == 1)
    assert(next(iter(found_values["CakeType"])) == "carrot")


def test_entity_finder_duplicate_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a chocolate cake and a chocolate biscuit")
    # This matches multiple, but unfortunately there's no order guarantee so it could match either
    cake = (found_text == "I want a @CakeType cake and a @CakeType biscuit")
    biscuit = (found_text == "I want a @Biscuit cake and a @Biscuit biscuit")
    assert(cake or biscuit)
    if cake:
        assert(len(found_values["CakeType"]) == 1)
        assert(next(iter(found_values["CakeType"])) == "chocolate")
    if biscuit:
        assert(len(found_values["Biscuit"]) == 1)
        assert(next(iter(found_values["Biscuit"])) == "chocolate")


def test_entity_finder_multiple_value_matches():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a Carrot cake and then a beer to drink")
    assert(found_text == "I want a @CakeType cake and then a @Drinks to drink")
    assert(len(found_values["CakeType"]) == 1)
    assert(next(iter(found_values["CakeType"])) == "carrot")
    assert(len(found_values["Drinks"]) == 1)
    assert(next(iter(found_values["Drinks"])) == "beer")


def test_entity_finder_case_insensitive():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a carrot cake")
    assert(found_text == "I want a @CakeType cake")
    assert(len(found_values["CakeType"]) == 1)
    assert(next(iter(found_values["CakeType"])) == "carrot")


def test_entity_finder_ignore_punctuation():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want a cake, maybe carrot?")
    assert(found_text == "I want a cake, maybe @CakeType?")
    assert(len(found_values["CakeType"]) == 1)
    assert(next(iter(found_values["CakeType"])) == "carrot")


def test_entity_finder_multi_word_values():
    finder = EntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_text, found_values = finder.replace_entity_values("I want some red wine and a cake")
    assert(found_text == "I want some @Drinks and a cake")
    assert(len(found_values["Drinks"]) == 1)
    assert(next(iter(found_values["Drinks"])) == "red wine")


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
