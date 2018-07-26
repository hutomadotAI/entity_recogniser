import pytest

import hu_entity.spacy_wrapper


@pytest.fixture(scope="module")
def spacy_wrapper():
    """EntityRecognizerServer takes ages to initialize, so define a single EntityRecognizerServer
    which will be reused in every test"""
    server = hu_entity.spacy_wrapper.SpacyWrapper(minimal_ers_mode=False)
    server.initialize()
    return server


def test_recognize_location(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("London")
    assert len(entity_list) == 1
    entity = entity_list[0]
    assert entity.entity_value == 'London'
    assert entity.spacy_category == 'GPE'
    assert entity.category == 'sys.places'
    assert entity.start_loc == 0
    assert entity.end_loc == 7


def test_recognize_person(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("Who is Sherlock Holmes")
    assert len(entity_list) == 1
    entity = entity_list[0]
    assert entity.entity_value == 'Sherlock Holmes'
    assert entity.spacy_category == 'PERSON'
    assert entity.category == 'sys.person'
    assert entity.start_loc == 7
    assert entity.end_loc == 22


def test_recognize_group(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("French bread")
    assert len(entity_list) == 1
    entity = entity_list[0]
    assert entity.entity_value == 'French'
    assert entity.spacy_category == 'NORP'
    assert entity.category == 'sys.group'
    assert entity.start_loc == 0
    assert entity.end_loc == 6


def test_recognize_fac(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("Golden Gate Bridge")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == 'Golden Gate Bridge'
    assert entity.spacy_category == 'FAC'
    assert entity.category == 'sys.places'
    assert entity.start_loc == 0
    assert entity.end_loc == 18


def test_recognize_org(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("Microsoft")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == 'Microsoft'
    assert entity.spacy_category == 'ORG'
    assert entity.category == 'sys.organization'
    assert entity.start_loc == 0
    assert entity.end_loc == 9


def test_recognize_loc(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("Rocky Mountain")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == 'Rocky Mountain'
    assert entity.spacy_category == 'LOC'
    assert entity.category == 'sys.places'
    assert entity.start_loc == 0
    assert entity.end_loc == 14


def test_ignore_event(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("World War 1")
    assert len(entity_list) == 0


def test_recognize_date(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("I would like to see you today")
    assert len(entity_list) == 1
    entity = entity_list[0]
    assert entity.entity_value == 'today'
    assert entity.spacy_category == 'DATE'
    assert entity.category == 'sys.date'
    assert entity.start_loc == 24
    assert entity.end_loc == 29


def test_recognize_date_2(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("23rd April 1852")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == '23rd April 1852'
    assert entity.spacy_category == 'DATE'
    assert entity.category == 'sys.date'
    assert entity.start_loc == 0
    assert entity.end_loc == 15


def test_recognize_time(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("1 hour")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "1 hour"
    assert entity.spacy_category == 'TIME'
    assert entity.category == 'sys.time'
    assert entity.start_loc == 0
    assert entity.end_loc == 6


def test_recognize_percent(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("99.13%")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "99.13%"
    assert entity.spacy_category == 'PERCENT'
    assert entity.category == 'sys.percent'
    assert entity.start_loc == 0
    assert entity.end_loc == 6


def test_recognize_money_as_number(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("$23.79")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "23.79"
    assert entity.spacy_category == 'MONEY'
    assert entity.category == 'sys.number'
    assert entity.start_loc == 1
    assert entity.end_loc == 6


def test_recognize_quantity_as_number(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("79 ounces")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "79 ounces"
    assert entity.spacy_category == 'QUANTITY'
    assert entity.category == 'sys.number'
    assert entity.start_loc == 0
    assert entity.end_loc == 9


def test_recognize_ordinal(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("thirteenth")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "thirteenth"
    assert entity.spacy_category == 'ORDINAL'
    assert entity.category == 'sys.ordinal'
    assert entity.start_loc == 0
    assert entity.end_loc == 10


def test_recognize_number_1(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("18")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "18"
    assert entity.spacy_category == 'CARDINAL'
    assert entity.category == 'sys.number'
    assert entity.start_loc == 0
    assert entity.end_loc == 2


def test_recognize_number_2(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("nine times")
    assert len(entity_list) == 1
    entity = entity_list[0]
    print(entity)
    assert entity.entity_value == "nine"
    assert entity.spacy_category == 'CARDINAL'
    assert entity.category == 'sys.number'
    assert entity.start_loc == 0
    assert entity.end_loc == 4


def test_does_not_recognize_stopwords_as_city(spacy_wrapper):
    entity_list, _ = spacy_wrapper.get_entities("London is a city")
    assert len(entity_list) == 1


