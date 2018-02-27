"""The named entity recognizer service"""
import argparse
import logging
import logging.config
import os
from pathlib import Path
import aiohttp
import traceback
from aiohttp import web
from nltk.corpus import stopwords

import spacy
import spacy.matcher
import yaml

from hu_entity.named_entity import NamedEntity
from hu_entity.named_entity import dumps_custom

DATA_DIR = Path(os.path.dirname(os.path.realpath(__file__)) + '/data')


def _get_logger():
    logger = logging.getLogger('hu_entity.server')
    return logger


CUSTOM_CITIES_TAG = "custom_cities"


def entity_to_string(ent):
    return "{{'{}', key:{}, ID:{}, at({}:{})}}".format(
        ent, ent.ent_id, ent.label, ent.start, ent.end)


class EntityRecognizerServer:
    def __init__(self, minimal_ers_mode=False):
        self.logger = _get_logger()
        # reads the spacy model
        if minimal_ers_mode:
            self.logger.warning("Loading minimal model...")
            self.nlp = spacy.load("en_core_web_sm")
        else:
            self.logger.warning("Loading full model...")
            self.nlp = spacy.load("en_core_web_md")
        # initialize the matcher with the model just read
        self.matcher = spacy.matcher.Matcher(self.nlp.vocab)
        self.nlp.vocab[CUSTOM_CITIES_TAG]
        self.CUSTOM_CITIES_ID = self.nlp.vocab[CUSTOM_CITIES_TAG].orth
        self.GPE_ID = self.nlp.vocab['GPE'].orth
        self.logger.warning('Entity ids: CUSTOM_CITIES={}, GPE={}'.format(
            self.CUSTOM_CITIES_ID, self.GPE_ID))

    def on_entity_match(self, matcher, doc, i, matches):
        """ merge phrases before they are added to the NER """
        match_id, start, end = matches[i]
        span = doc[start:end]
        match_text = span.text
        self.logger.info(
            "Custom entity candidate match for {'%s', key:%s, ID:%s, at(%s,%s)}",
            match_text, match_id, self.CUSTOM_CITIES_ID, start, end)

        candidate_entity = (match_id, self.CUSTOM_CITIES_ID, start, end)
        add_candidate = True

        # scan through existing entities and decide whether we want to keep them
        new_doc_ents = []
        for ent in doc.ents:
            add_this_entity = True
            ent_start = ent.start
            ent_end = ent.end
            if ((ent_start <= start and ent_end >= start)
                    or (ent_start < end and ent_end >= end)):
                # The existing entity wins if it is longer than the candidate
                # (at same length the candidate wins)
                if (ent_end - ent_start) > (end - start):
                    add_candidate = False
                else:
                    add_this_entity = False
                self.logger.info(
                    "Candidate clashes with existing entity %s, use candidate=%s",
                    entity_to_string(ent), add_candidate)

            if add_this_entity:
                new_doc_ents.append(ent)

        if add_candidate:
            new_doc_ents.append(candidate_entity)
        doc.ents = new_doc_ents

    def add_entity(self, entity, key):
        """ add a custom entity to the NER with key 'key' """
        terms = entity.split()

        word_specs = [{'LOWER': term.strip().lower()} for term in terms]
        # Changed in v2.0 https://spacy.io/api/matcher#add
        self.matcher.add(key, self.on_entity_match, word_specs)

    def initialize_NER_with_custom_locations(self):
        # set the custom entity to 0. We increment this number for each new entity so they
        # have a unique identifier
        # reads the city file
        city_path = DATA_DIR / 'cities1000.txt'
        self.logger.warning('Add custom locations from %s', city_path)

        # load cities into a set, to remove duplicates
        with city_path.open(encoding='utf8') as fp:
            cities_set = set()
            for line in fp:
                columns = line.split('\t')
                # gets the location name from the line just read
                location_name = columns[1]
                if len(location_name) > 3:
                    cities_set.add(location_name)

        stopw = set(stopwords.words('english'))
        # removes city names that can be confused with a stop word (ex. Is, As)
        # and cities with short names such as "see"
        key = 0
        for city in cities_set:
            if city not in stopw:
                self.add_entity(city, key)
                # increments the key
                key += 1
        return key

    def get_entities(self, q):
        # gets the 'q' parameter and initiates the NLP component
        doc = self.nlp(q)

        # instantiate the NER matcher
        self.matcher(doc)

        # list of all recognized entities
        entity_list = []
        for word in doc.ents:
            named_entity = NamedEntity(word.text, word.label_, word.start_char,
                                       word.end_char)
            if named_entity.category is not None:
                entity_list.append(named_entity)
            else:
                self.logger.info("Skipping uncategorized entity %s",
                                 named_entity)

        return entity_list

    async def handle(self, request):
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
        entities = self.get_entities(q)
        self.logger.info("Entities found: '%s'", entities)
        resp = web.json_response(entities, dumps=dumps_custom)
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
                             ExceptionWrappedCaller(er_server.handle))


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
    er_server.initialize_NER_with_custom_locations()

    initialize_web_app(web_app, er_server)
    parser = argparse.ArgumentParser(description="NER server")
    parser.add_argument('--port', type=int, default=9095)
    args = parser.parse_args()
    port = args.port

    logger.warning("Starting entity recognizer API on port %d", port)
    web.run_app(web_app, port=port)


if __name__ == '__main__':
    main()
