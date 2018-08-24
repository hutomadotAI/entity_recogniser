import json
import marisa_trie
import string
from collections import defaultdict


class EntityFinder:

    def __init__(self):
        self.entity_tries = {}
        self.punctuation = string.punctuation

    def setup_entity_values(self, entities):
        for entity_name, entity_values in entities.items():
            # This can be done more concisely, expanded for clarity
            updated_words = []
            for word in entity_values:
                lower = word.lower()
                temp_word = lower.strip(self.punctuation)
                updated_words.append(temp_word)

            self.entity_tries[entity_name] = marisa_trie.Trie(updated_words)

    def replace_entity_values(self, conversation):
        # Construct the list of values to match against
        words_to_find = self.split_message(conversation)
        entity_matches = defaultdict(list)
        words_matched = set()

        for word in words_to_find:
            compare_word = word.lower()
            compare_word = compare_word.strip(self.punctuation)
            if word not in words_matched:
                for entity_name, entity_trie in self.entity_tries.items():
                    if compare_word in entity_trie:
                        entity_matches[compare_word].append(entity_name)
                        words_matched.add(compare_word)

        return entity_matches

    def split_message(self, conversation):
        conversation_words = conversation.split()
        search_words = []

        # Iterate over all possible word permutations
        for start in range(0, len(conversation_words)):
            for end in range(start, len(conversation_words)):
                search_words.append(" ".join(conversation_words[start:end + 1]))

        return search_words
