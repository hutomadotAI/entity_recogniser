import argparse
import json
import os
from aiohttp import web
from pathlib import Path

import spacy
import en_core_web_md
import spacy.matcher

from hu_entity.named_entity import NamedEntity

DATA_DIR = Path(os.path.dirname(os.path.realpath(__file__)) + '/data')

class EntityRecognizerServer:

    def __init__(self):
        # reads the spacy model
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
        if len(terms) == 1:
            self.matcher.add(entity_key=str(key), label=lbl, attrs={}, specs=[[{spacy.attrs.ORTH: terms[0].strip()}]],
                        on_match=self.merge_phrases)

        if len(terms) == 2:
            self.matcher.add(entity_key=str(key), label=lbl, attrs={},
                        specs=[[{spacy.attrs.ORTH: terms[0].strip()}, {spacy.attrs.ORTH: terms[1].strip()}]],
                        on_match=self.merge_phrases)

        if len(terms) == 3:
            self.matcher.add(entity_key=str(key), label=lbl, attrs={}, specs=[
                [{spacy.attrs.ORTH: terms[0].strip()},
                {spacy.attrs.ORTH: terms[1].strip()},
                {spacy.attrs.ORTH: terms[2].strip()}]], 
                on_match=self.merge_phrases)

        if len(terms) == 4:
            self.matcher.add(entity_key=str(key), label=lbl, attrs={}, specs=[
                [{spacy.attrs.ORTH: terms[0].strip()},
                {spacy.attrs.ORTH: terms[1].strip()},
                {spacy.attrs.ORTH: terms[2].strip()},
                {spacy.attrs.ORTH: terms[3].strip()}]], 
                on_match=self.merge_phrases)


    def initialize_NER_with_custom_locations(self):
        # set the custom entity to 0. We increment this number for each new entity so they have a unique identifier
        key = 0

        # reads the city file
        city_path = DATA_DIR/'cities1000.txt'
        with city_path.open(encoding='utf8') as fp:
            for line in fp:
                columns = line.split('\t')
                # gets the location name from the line just read
                location_name = columns[1]
                if len(location_name) > 3:
                    self.add_entity(location_name, key, 'GPE')
                    # adds the entity all lower case. 
                    # This is needed so we can recognize both 'London' and 'london'
                    self.add_entity(location_name.lower(), key, 'GPE')
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
            e = NamedEntity(word.label_, word.text)
            entity_list.append(e)

        return entity_list


    async def handle(self, request):
        '''
        the function returns a collection of recognized entities as JSON response
        '''
        entities = self.get_entities(request.rel_url.query['q'])
        resp = web.Response()
        resp.text = json.dumps(entities)
        resp.content_type = 'application/json'
        return resp



def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NER server")
    parser.add_argument('--port', type=int, default=9095)
    args = parser.parse_args()

    er_server = EntityRecognizerServer()

    er_server.initialize_NER_with_custom_locations()
    app = web.Application()
    app.router.add_route('GET', '/ner', er_server.handle)
    web.run_app(app, port=args.port)


if __name__ == '__main__':
    main()
