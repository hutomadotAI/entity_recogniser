"""The named entity recognizer service"""
import argparse
import logging
import logging.config
import os
import aiohttp
import traceback
from aiohttp import web

import json


import yaml

from hu_entity.spacy_wrapper import SpacyWrapper
from hu_entity.named_entity import dumps_custom
from hu_entity.entity_finder import EntityFinder


def _get_logger():
    logger = logging.getLogger('hu_entity.server')
    return logger


class EntityRecognizerServer:
    def __init__(self, minimal_ers_mode=False):
        self.logger = _get_logger()
        self.spacy_wrapper = SpacyWrapper(minimal_ers_mode)
    
    def initialize(self):
        self.spacy_wrapper.initialize()
        
    async def handle_ner(self, request):
        '''
        the function returns a collection of recognized entities as JSON response
        '''
        url = request.url
        q = url.query.get('q', None)
        if q is None:
            self.logger.warning(
                'Invalid NER request, no q query parameter, url was %s', url)
            raise web.HTTPBadRequest()

        self.logger.info("Entity request '%s'", q)
        entities, _ = self.spacy_wrapper.get_entities(q)
        self.logger.info("Entities found: '%s'", entities)
        resp = web.json_response(entities, dumps=dumps_custom)
        return resp

    async def handle_tokenize(self, request):
        '''
        the function returns a collection of recognized entities as JSON response
        '''
        url = request.url
        q = url.query.get('q', None)
        filter_ents = url.query.get('filter_ents')
        sw_size = url.query.get('sw_size')
        if q is None:
            self.logger.warning(
                'Invalid NER request, no q query parameter, url was %s', url)
            raise web.HTTPBadRequest()

        self.logger.info("Tokenize request '%s'", q)
        tokens = self.spacy_wrapper.tokenize(q, filter_ents, sw_size)
        self.logger.info("Tokens found: '%s'", tokens)
        resp = web.json_response(tokens)
        return resp

    async def handle_findentities(self, request):
        '''
        the function returns the supplied chat text with the entities identified
        '''
        url = request.url
        if not request.can_read_body:
            self.logger.warning(
                'Invalid NER findentities request, no body found, url was %s', url)
            raise web.HTTPBadRequest

        body = await request.json()

        finder = EntityFinder()
        finder.setup_entity_values(body['entities'])
        output = finder.replace_entity_values(body['conversation'])
        data = {'conversation': output}
        resp = web.json_response(data)
        return resp

    async def handle_addentities(self, request):
        """
        this function allows to add entities to spacy matcher

        entity_value: str; value to add to entity category
        entity_key: str; category to which entity_value should be added
        """
        url = request.url
        if not request.can_read_body:
            self.logger.warning(
                'Invalid NER findentities request, no body found, url was %s', url)
            raise web.HTTPBadRequest

        body = await request.json()
        self.spacy_wrapper.add_entity(body['entity_value'],
                                      body['entity_key'])
        data = {'success': 'True'}
        resp = web.json_response(data)
        return resp


class ExceptionWrappedCaller:
    """Put an exception logging wrapper around all the endpoints.
       This is preferable to using aiohttp middleware as we control
       that here without upstream involvement"""

    def __init__(self, call_to_wrap):
        self.call_to_wrap = call_to_wrap
        self.logger = _get_logger()

    async def __call__(self, *args, **kwargs):
        try:
            response = await self.call_to_wrap(*args, **kwargs)
        except aiohttp.web_exceptions.HTTPException:
            # assume if we're throwing this that it's already logged
            raise
        except Exception as exc:
            self.logger.exception("Unexpected exception in call")

            error_string = "Internal Server Error\n" + traceback.format_exc()
            raise aiohttp.web_exceptions.HTTPInternalServerError(
                text=error_string)
        return response


def initialize_web_app(web_app, er_server):
    logger = _get_logger()
    logger.warning("Entity Recognizer initializing server.")
    web_app.router.add_route('GET', '/ner',
                             ExceptionWrappedCaller(er_server.handle_ner))
    web_app.router.add_route('GET', '/tokenize',
                             ExceptionWrappedCaller(er_server.handle_tokenize))
    web_app.router.add_route('POST', '/findentities',
                             ExceptionWrappedCaller(er_server.handle_findentities))
    web_app.router.add_route('GET', '/addentities',
                             ExceptionWrappedCaller(er_server.handle_addentities))


LOGGING_CONFIG_TEXT = """
version: 1
root:
  level: DEBUG
  handlers: ['console' ,'elastic']
formatters:
  default:
    format: "%(asctime)s.%(msecs)03d|%(levelname)s|%(name)s|%(message)s"
    datefmt: "%Y%m%d_%H%M%S"
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    stream: ext://sys.stdout
    formatter: default
  elastic:
    class: hu_logging.HuLogHandler
    level: INFO
    log_path: /tmp/hu_log
    log_tag: ENTITY
    es_log_index: entity-recog-v1
    multi_process: False
"""


def main():
    """Main function"""
    logging_config = yaml.load(LOGGING_CONFIG_TEXT)
    logging_config['handlers']['elastic']['elastic_search_url'] = \
        os.environ.get('LOGGING_ES_URL', None)
    logging.config.dictConfig(logging_config)

    web_app = web.Application()
    env_minimal_server_str = os.environ.get("ERS_MINIMAL_SERVER", "")

    logger = _get_logger()
    try:
        env_minimal_server_int = int(env_minimal_server_str)
    except ValueError:
        env_minimal_server_int = 0
        logger.warning("ERS_MINIMAL_SERVER not set or invalid '{}'".format(
            env_minimal_server_str))

    er_server = EntityRecognizerServer(env_minimal_server_int)
    er_server.initialize()

    initialize_web_app(web_app, er_server)
    parser = argparse.ArgumentParser(description="NER server")
    parser.add_argument('--port', type=int, default=9095)
    args = parser.parse_args()
    port = args.port

    logger.warning("Starting entity recognizer API on port %d", port)
    web.run_app(web_app, port=port)


if __name__ == '__main__':
    main()
