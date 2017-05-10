import pytest

import hu_entity.server as hu_s

# EntityRecognizerServer takes ages to initialize
@pytest.fixture(scope="module")
def ner_server():
    server = hu_s.EntityRecognizerServer()
    server.initialize_NER_with_custom_locations()
    return server

def test_recognize_location(ner_server):
    entity_list = ner_server.get_entities("Reading")
    assert entity_list[0].label == 'Reading'
    assert entity_list[0].named_entity == 'GPE'

def test_recognize_date(ner_server):
    entity_list = ner_server.get_entities("I would like to see you today")
    assert entity_list[0].label == 'today'
    assert entity_list[0].named_entity == 'DATE'


