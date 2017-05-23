"""The named entity recognizer service"""
import argparse
import logging
import os
from pathlib import Path
from aiohttp import web
from nltk.corpus import stopwords

import spacy
import spacy.matcher
import en_core_web_md

from hu_entity.named_entity import NamedEntity
from hu_entity.named_entity import dumps_custom

import hu_logging

DATA_DIR = Path(os.path.dirname(os.path.realpath(__file__)) + '/data')

def _get_logger():
    logger = hu_logging.get_logger('hu_entity.server', console_log_level=logging.INFO)
    return logger

class EntityRecognizerServer:

    def __init__(self, minimal_ers_mode=False):
        self.logger = _get_logger()
        # reads the spacy model
        if minimal_ers_mode:
            self.logger.warning("Loading minimal model...")
            self.nlp = spacy.load("en")
        else:
            self.logger.warning("Loading full model...")
            self.nlp = en_core_web_md.load()
        # initialize the matcher with the model just read
        self.matcher = spacy.matcher.Matcher(self.nlp.vocab)


    def merge_phrases(self, matcher, doc, i, matches):
        """ merge phrases before they are added to the NER """
        if i != len(matches) - 1:
            return None
        spans = [(ent_id, label, doc[start: end]) for ent_id, label, start, end in matches]
        for ent_id, label, span in spans:
            span.merge('NNP' if label else span.root.tag_, span.text, self.nlp.vocab.strings[label])


    def add_entity(self, entity, key, lbl):
        """ add a custom entity to the NER with key 'key' and label 'lbl' """
        terms = entity.split()

        specs = [[{spacy.attrs.ORTH: term.strip()} for term in terms]]
        self.matcher.add(entity_key=str(key), label=lbl, attrs={}, specs=specs,
            on_match=self.merge_phrases)

    def initialize_NER_with_custom_locations(self):
        # set the custom entity to 0. We increment this number for each new entity so they have a unique identifier
        key = 0
        stopw = set(stopwords.words('english'))
        # reads the city file
        city_path = DATA_DIR/'cities1000.txt'
        self.logger.warning('Add custom locations from %s', city_path)
        with city_path.open(encoding='utf8') as fp:
            for line in fp:
                columns = line.split('\t')
                # gets the location name from the line just read
                location_name = columns[1]
                # removes city names that can be confused with a stop word (ex. Is, As)
                # and cities with short names such as "see"
                if location_name.lower() not in stopw and len(location_name) > 3:
                    self.add_entity(location_name, key, 'custom_cities')
                    # adds the entity all lower case.
                    # This is needed so we can recognize both 'London' and 'london'
                    self.add_entity(location_name.lower(), key, 'custom_cities')
                    # increaments the key
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
            named_entity = NamedEntity(word.text, word.label_, word.start_char, word.end_char)
            if named_entity.category is not None:
                entity_list.append(named_entity)
            else:
                self.logger.info("Skipping uncategorized entity %s", named_entity)

        return entity_list


    async def handle(self, request):
        '''
        the function returns a collection of recognized entities as JSON response
        '''
        url = request.url
        q = url.query.get('q', None)
        if q is None:
            self.logger.warning('Invalid NER request, no q query parameter, url was %s',
                                url)
            raise web.HTTPBadRequest()

        self.logger.info("Entity request '%s'", q)
        entities = self.get_entities(q)
        self.logger.info("Entities found: '%s'", entities)
        resp = web.json_response(entities, dumps=dumps_custom)
        return resp


def initialize_web_app(web_app, er_server):
    logger = _get_logger()
    logger.warning("Entity Recognizer initializing server.")
    web_app.router.add_route('GET', '/ner', er_server.handle)

def main():
    """Main function"""
    hu_logging.initialize_logging('/tmp/hu_entity_log', "NER")
    web_app = web.Application()
    env_minimal_server_str = os.environ.get("ERS_MINIMAL_SERVER", None)

    logger = _get_logger()
    try:
        env_minimal_server_int = int(env_minimal_server_str)
    except ValueError:
        env_minimal_server_int = 0
        logger.warning("ERS_MINIMAL_SERVER not set or invalid '{}'".format(env_minimal_server_str))

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
