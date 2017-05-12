import pytest
from aiohttp import web

import hu_entity.server as hu_s

@pytest.fixture(scope="module")
def ner_server():
    """EntityRecognizerServer takes ages to initialize, so define a single EntityRecognizerServer
    which will be reused in every test"""
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

@pytest.fixture()
def cli(loop, test_client, ner_server):
    """Defines the CLI test HTTP client which will start a test HTTP server.
    Will reuse the module level ner_server pytest fixture which is the slow bit to initialize"""
    web_app = web.Application(loop=loop)
    hu_s.initialize_web_app(web_app, ner_server)
    return loop.run_until_complete(test_client(web_app))

async def test_server_root_404(cli):
    resp = await cli.get('/')
    assert resp.status == 404

async def test_server_ner_no_q_400(cli):
    resp = await cli.get('/ner')
    assert resp.status == 400

async def test_server_ner_q_1(cli):
    resp = await cli.get('/ner?q=Reading')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['named_entity'] == "GPE"
    assert item['label'] == "Reading"

async def test_server_ner_no_entity(cli):
    resp = await cli.get('/ner?q=Nothing')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 0

async def test_server_ner_multi_instance(cli):
    resp = await cli.get('/ner?q=What weather is it in Reading tomorrow')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 2
    item = json_resp[0]
    assert item['named_entity'] == "GPE"
    assert item['label'] == "Reading"
    item = json_resp[1]
    assert item['named_entity'] == "DATE"
    assert item['label'] == "tomorrow"