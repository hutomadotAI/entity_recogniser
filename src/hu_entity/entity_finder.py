import marisa_trie
import string
import re
import sre_constants
import logging
from collections import defaultdict


def _get_logger():
    logger = logging.getLogger('hu_entity.entity_finder')
    return logger


class EntityFinder:

    def __init__(self):
        self.logger = _get_logger()
        self.entity_tries = {}
        self.punctuation = string.punctuation
        self.regex_entities = {}

    def setup_entity_values(self, entities):
        self.logger.info("Setting up value entities'%s'", entities)
        for entity_name, entity_values in entities.items():
            # This can be done more concisely, expanded for clarity
            updated_words = []
            for word in entity_values:
                lower = word.lower()
                temp_word = lower.strip(self.punctuation)
                updated_words.append(temp_word)

            self.entity_tries[entity_name] = marisa_trie.Trie(updated_words)

    def setup_regex_entities(self, regex_entities):
        self.logger.info("Setting up regex entities '%s'", regex_entities)
        regex_good = True
        try:
            for entity_name, entity_regex in regex_entities.items():
                self.logger.debug("Compiling regex entity '%s'", entity_regex)
                compiled = re.compile(entity_regex)
                self.regex_entities[entity_name] = compiled
        except re.error:
            self.logger.warn("Caught re.error in setup_regex_entities")
            regex_good = False
        except sre_constants.error:
            self.logger.warn("Caught sre_constants.error in setup_regex_entities")
            regex_good = False
        except Exception:
            self.logger.warn("Caught Exception in setup_regex_entities")
            regex_good = False
        return regex_good

    def find_entity_values(self, conversation):
        # Construct the list of values to match against
        words_to_find_list = self.split_message(conversation)
        words_to_find_regex = conversation.split()
        candidate_matches_list = defaultdict(list)
        candidate_matches_regex = defaultdict(list)

        entity_matches = defaultdict(list)
        words_matched = set()

        # Examine value type entities
        candidate_matches_list, words_matched = \
            self.match_value_entities(candidate_matches_list, words_matched, words_to_find_list)

        # Examine regex type entities
        candidate_matches_regex, words_matched =\
            self.match_regex_entities(candidate_matches_regex, words_matched, words_to_find_regex)

        # Ensure only the longest match is counted for list type entities
        for entity_name, candidate_words in candidate_matches_list.items():
            longest_word = candidate_words[0]
            for candidate_word in candidate_words:
                if len(candidate_word) > len(longest_word):
                    longest_word = candidate_word
            entity_matches[longest_word].append(entity_name)

        # Include regex type entities
        for entity_name, candidate_words in candidate_matches_regex.items():
            for candidate_word in candidate_words:
                entity_matches[candidate_word].append(entity_name)

        return entity_matches

    def match_regex_entities(self, candidate_matches_regex, words_matched, words_to_find_regex):
        for word in words_to_find_regex:
            compare_word_original = word.strip(self.punctuation)
            if word not in words_matched:
                match_found = False
                for entity_name, compiled in self.regex_entities.items():
                    if compiled.fullmatch(compare_word_original):
                        candidate_matches_regex[entity_name].append(compare_word_original)
                        match_found = True
                if match_found:
                    words_matched.add(compare_word_original)
        return candidate_matches_regex, words_matched

    def match_value_entities(self, candidate_matches_list, words_matched, words_to_find_list):
        for word in words_to_find_list:
            compare_word_original = word.strip(self.punctuation)
            compare_word = compare_word_original.lower()
            if word not in words_matched:
                match_found = False
                for entity_name, entity_trie in self.entity_tries.items():
                    if compare_word in entity_trie:
                        candidate_matches_list[entity_name].append(compare_word_original)
                        match_found = True
                if match_found:
                    words_matched.add(compare_word_original)
        return candidate_matches_list, words_matched

    def split_message(self, conversation):
        conversation_words = conversation.split()
        search_words = []

        # Iterate over all possible word permutations
        for start in range(0, len(conversation_words)):
            for end in range(start, len(conversation_words)):
                search_words.append(" ".join(conversation_words[start:end + 1]))

        return search_words
