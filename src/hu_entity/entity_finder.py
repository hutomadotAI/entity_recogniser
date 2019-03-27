import datrie
import string
import logging
from collections import defaultdict


def _get_logger():
    logger = logging.getLogger('hu_entity.entity_finder')
    return logger


class EntityFinder:

    def __init__(self):
        self.logger = _get_logger()
        self.dentity_tries = {}
        self.punctuation = string.punctuation
        self.regex_entities = {}

    def setup_cached_entity_values(self, entities):
        self.logger.info("Caching value entities")
        for entity_name, entity_values in entities.items():
            # This can be done more concisely, expanded for clarity
            updated_words = []
            for word in entity_values:
                lower = word.lower()
                temp_word = lower.strip(self.punctuation)
                updated_words.append(temp_word)

            if(entity_name in self.dentity_tries):
                for word in updated_words:
                    self.dentity_tries[entity_name][word] = True
            else:
                # its a new trie
                self.dentity_tries[entity_name] = datrie.Trie(string.printable)
                for word in updated_words:
                    self.dentity_tries[entity_name][word] = True

            self.logger.info("updated " + entity_name + " trie, now contains "
                             + str(len(self.dentity_tries[entity_name])))
            self.logger.info("currently have " + str(len(self.dentity_tries)) + " entities")

    def delete_cached_entity_values(self, entities):
        self.logger.info("Clearing value entities")
        for entity_name, entity_values in entities.items():
            if(entity_name in self.dentity_tries):
                del self.dentity_tries[entity_name]

            self.logger.info("currently have " + str(len(self.dentity_tries)) + " entities")

    def find_entity_values(self, conversation):
        # Construct the list of values to match against
        words_to_find_list = self.split_message(conversation)
        candidate_matches_list = defaultdict(list)

        entity_matches = defaultdict(list)
        words_matched = set()

        # Examine value type entities
        candidate_matches_list, words_matched = \
            self.match_value_entities(candidate_matches_list, words_matched, words_to_find_list)

        # Ensure only the longest match is counted for list type entities
        for entity_name, candidate_words in candidate_matches_list.items():
            longest_word = candidate_words[0]
            for candidate_word in candidate_words:
                if len(candidate_word) > len(longest_word):
                    longest_word = candidate_word
            entity_matches[longest_word].append(entity_name)

        return entity_matches

    def match_value_entities(self, candidate_matches_list, words_matched, words_to_find_list):
        for word in words_to_find_list:
            compare_word_original = word.strip(self.punctuation)
            compare_word = compare_word_original.lower()
            if word not in words_matched:
                match_found = False
                for entity_name, entity_trie in self.dentity_tries.items():
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
