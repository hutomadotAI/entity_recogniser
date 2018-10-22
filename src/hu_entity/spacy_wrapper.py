import logging
import enum
from pathlib import Path
import os
import string

from nltk.corpus import stopwords

import spacy
import spacy.matcher

from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from hu_entity.named_entity import NamedEntity

DATA_DIR = Path(os.path.dirname(os.path.realpath(__file__)) + '/data')


class StopWordSize(enum.Enum):
    """Stopword size"""
    SMALL = 1
    LARGE = 2
    XLARGE = 3


class SpacyException(Exception):
    pass


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
    def __init__(self, minimal_ers_mode="False", language='en'):
        self.logger = _get_logger()
        self.minimal_ers_mode = minimal_ers_mode
        self.language = language
        self.tokenizer_stoplist_xlarge = None
        self.tokenizer_stoplist_large = None
        self.tokenizer_stoplist = None
        self.tokenizer_symbols = None
        self.nlp = None
        self.matcher = None
        self.GPE_ID = None
        self.PERSON_ID = None

    def reload_model(self, minimal_ers_mode, language):
        self.minimal_ers_mode = minimal_ers_mode
        self.language = language
        self.initialize()

    def __load_model(self, minimal_ers_mode, language):
        model_lookup = {
            "en": ["en_core_web_sm", "en_core_web_md"],
            "es": ["es_core_news_sm", "es_core_news_md"],
            "fr": ["fr_core_news_sm", "fr_core_news_md"],
            "pt": ["pt_core_news_sm"],
            "it": ["it_core_news_sm"],
            "nl": ["nl_core_news_sm"]
        }

        try:
            language_models = model_lookup[language]
        except (KeyError) as exc:
            raise SpacyException(
                "Language {} is not available".format(language))

        if minimal_ers_mode == "True":
            self.logger.warning(
                "Loading minimal model for {}...".format(language))
            model = language_models[language][0]
        else:
            if len(language_models) > 1:
                self.logger.warning("Loading model in {}...".format(language))
                model = language_models[1]
            else:
                self.logger.warning(
                    "Loading model in {} (fallback minimal model)...".format(
                        language))
                model = language_models[0]

        self.logger.info("Loading Spacy model {}...".format(model))
        return spacy.load(model)

    def on_entity_match(self, matcher, doc, i, matches, entity_id):
        """ merge phrases before they are added to the NER """
        match_id, start, end = matches[i]
        span = doc[start:end]
        match_text = span.text
        self.logger.info(
            "Custom entity candidate match for {'%s', key:%s, ID:%s, at(%s,%s)}",
            match_text, match_id, entity_id, start, end)

        candidate_entity = (match_id, entity_id, start, end)
        add_candidate = True

        # scan through existing entities and decide whether we want to keep them
        new_doc_ents = []
        for ent in doc.ents:
            add_this_entity = True
            ent_start = ent.start
            ent_end = ent.end
            if ((ent_start <= start < ent_end)
                    or (ent_start < end <= ent_end)):
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
        custom_id = self.nlp.vocab[key].orth
        terms = entity.split()

        word_specs = [{'LOWER': term.strip().lower()} for term in terms]
        self.logger.info("custom_id for {} is {}".format(key, custom_id))
        self.logger.info("word_specs: {}".format(word_specs))
        # Changed in v2.0 https://spacy.io/api/matcher#add
        self.matcher.add(
            entity,
            lambda m, d, i, ms: self.on_entity_match(m, d, i, ms, entity_id=custom_id),
            word_specs)

    def initialize(self):
        # reads the spacy model
        self.nlp = self.__load_model(self.minimal_ers_mode, self.language)
        # initialize the matcher with the model just read
        self.matcher = spacy.matcher.Matcher(self.nlp.vocab)
        self.GPE_ID = self.nlp.vocab['GPE'].orth
        self.PERSON_ID = self.nlp.vocab['PERSON'].orth
        self.logger.warning('Entity ids: GPE={}'.format(self.GPE_ID))

        language = self.language
        if language == 'en':
            # A custom stoplist taken from sklearn.feature_extraction.stop_words import
            # ENGLISH_STOP_WORDS
            custom_stoplist = {
                'much', 'herein', 'thru', 'per', 'somehow', 'throughout',
                'almost', 'somewhere', 'whereafter', 'nevertheless', 'indeed',
                'hereby', 'across', 'within', 'co', 'yet', 'elsewhere',
                'whence', 'seeming', 'un', 'whither', 'mine', 'whether',
                'also', 'thus', 'amongst', 'thereafter', 'mostly', 'amoungst',
                'therefore', 'seems', 'something', 'thereby', 'others',
                'hereupon', 'us', 'everyone', 'perhaps', 'please', 'hence',
                'due', 'seemed', 'else', 'beside', 'therein', 'couldnt',
                'moreover', 'anyway', 'whatever', 'anyhow', 'de', 'among',
                'besides', 'though', 'either', 'rather', 'might', 'noone',
                'eg', 'thereupon', 'may', 'namely', 'ie', 'sincere', 'whereby',
                'con', 'latterly', 'becoming', 'meanwhile', 'afterwards',
                'thence', 'whoever', 'otherwise', 'anything', 'however',
                'whereas', 'although', 'hereafter', 'already', 'beforehand',
                'etc', 'whenever', 'even', 'someone', 'whereupon', 'inc',
                'sometimes', 'ltd', 'cant'
            }
            nltk_stopwords = set(stopwords.words('english'))

            excluded_tokenizer_stopwords = {
                'why', 'when', 'where', 'why', 'how', 'which', 'what', 'whose',
                'whom'
            }

            self.tokenizer_stoplist_xlarge = (nltk_stopwords
                                              | ENGLISH_STOP_WORDS
                                              | {"n't", "'s", "'m", "ca"})

            self.tokenizer_stoplist_large = (nltk_stopwords | custom_stoplist
                                             | {"n't", "'s", "'m", "ca"}) - \
                                            excluded_tokenizer_stopwords

            self.tokenizer_stoplist = set()

            # List of symbols we don't care about
            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"', "'ve"
            ]
        elif language == 'es':
            self.tokenizer_stoplist = self.tokenizer_stoplist_large = set()
            self.tokenizer_stoplist_xlarge = set(stopwords.words('spanish'))

            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"', "¿"
            ]
        elif language == 'fr':
            self.tokenizer_stoplist = self.tokenizer_stoplist_large =\
                self.tokenizer_stoplist_xlarge = set(stopwords.words('french'))

            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"'
            ]
        elif language == 'it':
            self.tokenizer_stoplist = self.tokenizer_stoplist_large =\
                self.tokenizer_stoplist_xlarge = set(stopwords.words('italian'))

            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"'
            ]
        elif language == 'pt':
            self.tokenizer_stoplist = self.tokenizer_stoplist_large =\
                self.tokenizer_stoplist_xlarge = set(stopwords.words('portuguese'))

            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"'
            ]
        elif language == 'nl':
            self.tokenizer_stoplist = self.tokenizer_stoplist_large =\
                self.tokenizer_stoplist_xlarge = set(stopwords.words('dutch'))

            self.tokenizer_symbols = [char for char in string.punctuation] + [
                "-----", "---", "...", "“", "”", '"'
            ]

    def get_entities(self, q):
        # gets the 'q' parameter and initiates the NLP component
        doc = self.nlp(q)

        # instantiate the NER matcher
        self.matcher(doc)
        self.logger.info("entities: {}".format(doc.ents))
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

    def lemma_and_remove_stopwords(self, tokens, sw_size):
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
        if sw_size is StopWordSize.XLARGE:
            sw = self.tokenizer_stoplist_xlarge
        elif sw_size is StopWordSize.LARGE:
            sw = self.tokenizer_stoplist_large
        elif sw_size is StopWordSize.SMALL:
            sw = self.tokenizer_stoplist
        else:
            raise SpacyException("Invalid StopWordSize {}".format(sw_size))
        tokens = [tok for tok in tokens if tok not in sw]

        if len(tokens) == 0:
            tokens = ['UNK']
        return tokens

    def tokenize(self, sample: str, filter_ents: bool, sw_size: StopWordSize):
        _, tokens = self.get_entities(sample)
        if filter_ents:
            tokens = self.filter_tokens(tokens, is_number_token, "NUM")
            self.logger.info("removed numbers: {}".format(tokens))
            tokens = self.filter_tokens(
                tokens,
                lambda token: is_entity_token_type(token, self.PERSON_ID),
                "PERSON")
            self.logger.info("removed persons: {}".format(tokens))
        tokens = self.lemma_and_remove_stopwords(tokens, sw_size)
        return tokens
