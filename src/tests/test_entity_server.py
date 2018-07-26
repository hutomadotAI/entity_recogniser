import pytest
from aiohttp import web
import hu_entity.server


@pytest.fixture(scope="module")
def ner_server():
    """EntityRecognizerServer takes ages to initialize, so define a single EntityRecognizerServer
    which will be reused in every test"""
    server = hu_entity.server.EntityRecognizerServer(minimal_ers_mode=True)
    server.initialize()
    return server


@pytest.fixture()
def cli(loop, test_client, ner_server):
    """Defines the CLI test HTTP client which will start a test HTTP server.
    Will reuse the module level ner_server pytest fixture which is the slow bit to initialize"""
    web_app = web.Application(loop=loop)
    hu_entity.server.initialize_web_app(web_app, ner_server)
    return loop.run_until_complete(test_client(web_app))


async def test_server_root_404(cli):
    resp = await cli.get('/')
    assert resp.status == 404


async def test_server_ner_no_q_400(cli):
    resp = await cli.get('/ner')
    assert resp.status == 400


async def test_server_ner_q_1(cli):
    resp = await cli.get('/ner?q=London')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "London"
    assert item['start'] == 0
    assert item['end'] == 7


async def test_server_ner_no_entity(cli):
    resp = await cli.get('/ner?q=Nothing')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 0


async def test_server_ner_multi_instance(cli):
    resp = await cli.get('/ner?q=What weather is it in London tomorrow')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 2
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "London"
    assert item['start'] == 22
    assert item['end'] == 29
    item = json_resp[1]
    assert item['category'] == "sys.date"
    assert item['value'] == "tomorrow"
    assert item['start'] == 30
    assert item['end'] == 38


async def test_server_ner_two_word_places(cli):
    resp = await cli.get('/ner?q=Whats the weather in New York')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "New York"


async def test_server_ner_mixed_case_places(cli):
    resp = await cli.get('/ner?q=Whats the weather in LonDON')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "LonDON"


async def test_server_tokenize(cli):
    resp = await cli.get('/tokenize?q=hi')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    assert json_resp[0] == "hi"
