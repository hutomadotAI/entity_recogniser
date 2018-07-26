import logging
from pathlib import Path
import os
import string

from nltk.corpus import stopwords

import spacy
import spacy.matcher

from hu_entity.named_entity import NamedEntity

CUSTOM_CITIES_TAG = "custom_cities"
DATA_DIR = Path(os.path.dirname(os.path.realpath(__file__)) + '/data')


def _get_logger():
    logger = logging.getLogger('hu_entity.spacy_wrapper')
    return logger


def entity_to_string(ent):
    return "{{'{}', key:{}, ID:{}, at({}:{})}}".format(
        ent, ent.ent_id, ent.label, ent.start, ent.end)


def is_number_token(token):
    try:
        float(token.text)
    except ValueError:
        return False
    return True


def is_entity_token_type(token, entity_type):
    is_entity_type = token.ent_type == entity_type
    return is_entity_type


class PlaceholderToken:
    """Placeholder token for fallback, emulate a spacy.tokens.Token"""
    def __init__(self, text, pos):
        self.text = text
        self.ent_type = -1
        self.pos = pos

    @property
    def lemma_(self):
        return self.text


class SpacyWrapper:
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
        self.PERSON_ID = self.nlp.vocab['PERSON'].orth
        self.logger.warning('Entity ids: CUSTOM_CITIES={}, GPE={}'.format(
            self.CUSTOM_CITIES_ID, self.GPE_ID))
        self.stoplist = None
        self.symbols = None

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
            if ((ent_start <= start and ent_end > start)
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

    def initialize(self):
        # A custom stoplist taken from sklearn.feature_extraction.stop_words import
        # ENGLISH_STOP_WORDS
        custom_stoplist = set([
            'much', 'herein', 'thru', 'per', 'somehow', 'throughout', 'almost',
            'somewhere', 'whereafter', 'nevertheless', 'indeed', 'hereby',
            'across', 'within', 'co', 'yet', 'elsewhere', 'whence', 'seeming',
            'un', 'whither', 'mine', 'whether', 'also', 'thus', 'amongst',
            'thereafter', 'mostly', 'amoungst', 'therefore', 'seems',
            'something', 'thereby', 'others', 'hereupon', 'us', 'everyone',
            'perhaps', 'please', 'hence', 'due', 'seemed', 'else', 'beside',
            'therein', 'couldnt', 'moreover', 'anyway', 'whatever', 'anyhow',
            'de', 'among', 'besides', 'though', 'either', 'rather', 'might',
            'noone', 'eg', 'thereupon', 'may', 'namely', 'ie', 'sincere',
            'whereby', 'con', 'latterly', 'becoming', 'meanwhile',
            'afterwards', 'thence', 'whoever', 'otherwise', 'anything',
            'however', 'whereas', 'although', 'hereafter', 'already',
            'beforehand', 'etc', 'whenever', 'even', 'someone', 'whereupon',
            'inc', 'sometimes', 'ltd', 'cant'
        ])
        nltk_stopwords = set(stopwords.words('english'))

        excluded_tokenizer_stopwords = set([
            'why', 'when', 'where', 'why', 'how', 'which', 'what', 'whose',
            'whom'
        ])

        self.tokenizer_stoplist = (nltk_stopwords | custom_stoplist
                                   | set(["n't", "'s", "'m", "ca"
                                          ])) - excluded_tokenizer_stopwords

        # List of symbols we don't care about
        self.tokenizer_symbols = [char for char in string.punctuation] + [
            "-----", "---", "...", "“", "”", '"', "'ve"
        ]

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

        # removes city names that can be confused with a stop word (ex. Is, As)
        # and cities with short names such as "see"
        key = 0
        for city in cities_set:
            if city not in nltk_stopwords:
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

        return (entity_list, doc)

    def filter_tokens(self, tokens, test_function, fallback_string):
        filtered_tokens = []
        found_token = False

        # filter out number tokens
        for token in tokens:
            if test_function(token):
                found_token = True
            else:
                filtered_tokens.append(token)

        # make sure that we keep at least one token after filtering
        if found_token and len(filtered_tokens) == 0:
            fallback_token = PlaceholderToken(fallback_string, 0)
            filtered_tokens = [fallback_token]

        return filtered_tokens

    def lemma_and_remove_stopwords(self, tokens):
        # lemmatize what's left
        lemmas = []
        for tok in tokens:
            if tok.lemma_ != "-PRON-":
                lemmas.append(tok.lemma_.lower().strip())
            else:
                lemmas.append(tok.lower_)

        tokens = lemmas

        # stoplist symbols
        tokens = [tok for tok in tokens if tok not in self.tokenizer_symbols]

        # stoplist the tokens
        tmp = [tok for tok in tokens if tok not in self.tokenizer_stoplist]
        if len(tmp) > 0:
            tokens = tmp
        return tokens

    def tokenize(self, sample: str):
        _, tokens = self.get_entities(sample)
        tokens = self.filter_tokens(tokens, is_number_token, "NUM")
        tokens = self.filter_tokens(
            tokens, lambda token: is_entity_token_type(token, self.PERSON_ID),
            "PERSON")
        tokens = self.lemma_and_remove_stopwords(tokens)
        return tokens
