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
        values = defaultdict(list)
        matches = defaultdict(set)
        matches_to_replace = defaultdict(list)

        for word in words_to_find:
            compare_word = word.lower()
            compare_word = compare_word.strip(self.punctuation)
            for entity_name, entity_trie in self.entity_tries.items():
                if compare_word in entity_trie:
                    matches[compare_word].add(entity_name)
                    matches_to_replace[compare_word].append(word)

        # Construct return values
        for entity_value, entity_names in matches.items():
            # length 0 means no matches, do nothing
            # for now, also dont do anything if there's duplicates
            if len(entity_names) == 1:
                entity_name = next(iter(entity_names))
                entity_name_string = "@" + entity_name
                value_to_replace = entity_value
                value_to_replace = value_to_replace.strip(self.punctuation)

                # Replace the values in the conversation string
                for word_to_replace in matches_to_replace[entity_value]:
                    conversation = conversation.replace(word_to_replace.strip(self.punctuation), entity_name_string)
                # Store the entity data
                values[entity_name].append(value_to_replace)

        return conversation, values

    def split_message(self, conversation):
        conversation_words = conversation.split()
        search_words = []

        # Iterate over all possible word permutations
        for start in range(0, len(conversation_words)):
            for end in range(start, len(conversation_words)):
                search_words.append(" ".join(conversation_words[start:end + 1]))

        return search_words
