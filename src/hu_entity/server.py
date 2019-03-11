"""The named entity recognizer service"""
import argparse
import logging
import logging.config
import os
import pathlib

import aiohttp
import traceback
from aiohttp import web

import yaml

from hu_entity.spacy_wrapper import SpacyWrapper, StopWordSize
from hu_entity.named_entity import dumps_custom
from hu_entity.entity_finder import EntityFinder


def _get_logger():
    logger = logging.getLogger('hu_entity.server')
    return logger


class EntityRecognizerServer:
    def __init__(self, minimal_ers_mode=False, language='en'):
        self.logger = _get_logger()
        self.spacy_wrapper = SpacyWrapper(minimal_ers_mode, language)

    def initialize(self):
        self.spacy_wrapper.initialize()

    async def reload(self, request):
        """
        allows loading a spacy model with, e.g. a different language
        """
        data = await request.json()
        if 'lang' not in data or 'minimal_ers_mode' not in data:
            raise web.HTTPBadRequest()
        size = data['minimal_ers_mode']
        lang = data['lang']
        self.spacy_wrapper.reload_model(minimal_ers_mode=size,
                                        language=lang)
        return web.Response()

    async def health(self, request):
        """
        health endpoint, just respond 200
        """
        return web.Response()

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
        filter_ents_str = url.query.get('filter_ents')
        sw_size_str = url.query.get('sw_size')
        if filter_ents_str is not None and filter_ents_str.lower() == "true":
            filter_ents = True
        else:
            filter_ents = False

        if sw_size_str is None:
            sw_size = StopWordSize.SMALL
        else:
            sw_size = StopWordSize[sw_size_str.upper()]

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
                'Invalid NER findentities request, no body found, url was %s',
                url)
            raise web.HTTPBadRequest

        body = await request.json()
        print(body)

        self.logger.info("Find entity request, populating entities")
        finder = EntityFinder()
        regex_good = True
        if 'entities' in body:
            self.logger.info("List entities found")
            finder.setup_entity_values(body['entities'])
        if 'regex_entities' in body:
            self.logger.info("Regex entities found")
            regex_good = finder.setup_regex_entities(body['regex_entities'])

        if not regex_good:
            self.logger.info('Invalid regex found in findentities')
            raise web.HTTPBadRequest(reason='Invalid regex found')
        else:
            self.logger.info('No regex submitted or regex compiled')

        self.logger.info("Find entity request, matching entities")
        values = finder.find_entity_values(body['conversation'])
        data = {'conversation': body['conversation'], 'entities': values}
        resp = web.json_response(data)

        return resp


@web.middleware
async def log_error_middleware(request, handler):
    try:
        response = await handler(request)
    except aiohttp.web_exceptions.HTTPException:
        # assume if we're throwing this that it's already logged
        raise
    except Exception:
        _get_logger().exception("Unexpected exception in call")

        error_string = "Internal Server Error\n" + traceback.format_exc()
        raise aiohttp.web_exceptions.HTTPInternalServerError(
            text=error_string)
    return response


def initialize_web_app(web_app, er_server):
    logger = _get_logger()
    logger.warning("Entity Recognizer initializing server.")
    web_app.middlewares.append(log_error_middleware)
    web_app.router.add_route('GET', '/health', er_server.health)
    web_app.router.add_route('GET', '/ner', er_server.handle_ner)
    web_app.router.add_route('GET', '/tokenize', er_server.handle_tokenize)
    web_app.router.add_route(
        'POST', '/findentities', er_server.handle_findentities)
    web_app.router.add_route('POST', '/reload', er_server.reload)


LOGGING_CONFIG_TEXT = """
version: 1
root:
  level: DEBUG
  handlers: ['console']
formatters:
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: "(asctime) (levelname) (name) (message)"
filters:
    emblogfilter:
        (): hu_entity.server.ErLogFilter
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    stream: ext://sys.stdout
    formatter: json
    filters: [emblogfilter]
"""


class ErLogFilter(logging.Filter):
    def __init__(self):
        self.language = os.environ.get("ERS_LANGUAGE", "en")
        self.version = os.environ.get("ERS_VERSION", None)

    def filter(self, record):
        """Add language, and if available, the version"""
        record.er_language = self.language
        if self.version:
            record.er_version = self.version
        return True


def main():
    """Main function"""
    logging_config_file = os.environ.get("LOGGING_CONFIG_FILE", None)
    if logging_config_file:
        logging_config_path = pathlib.Path(logging_config_file)
        with logging_config_path.open() as file_handle:
            logging_config = yaml.safe_load(file_handle)
    else:
        logging_config = yaml.load(LOGGING_CONFIG_TEXT)
    print("*** LOGGING CONFIG ***")
    print(logging_config)
    print("*** LOGGING CONFIG ***")
    logging.config.dictConfig(logging_config)

    web_app = web.Application()
    env_minimal_server_str = os.environ.get("ERS_MINIMAL_SERVER", "")
    env_language = os.environ.get("ERS_LANGUAGE", "en")

    logger = _get_logger()
    try:
        env_minimal_server_int = int(env_minimal_server_str)
    except ValueError:
        env_minimal_server_int = 0
        logger.warning("ERS_MINIMAL_SERVER not set or invalid '{}'".format(
            env_minimal_server_str))

    env_minimal_server = bool(env_minimal_server_int)
    er_server = EntityRecognizerServer(env_minimal_server,
                                       language=env_language)
    er_server.initialize()

    initialize_web_app(web_app, er_server)
    parser = argparse.ArgumentParser(description="NER server")
    parser.add_argument('--port', type=int, default=9095)
    args = parser.parse_args()
    port = args.port

    logger.warning("Starting entity recognizer API on port %d", port, extra={"port": port})
    web.run_app(web_app, port=port)


if __name__ == '__main__':
    main()
