import json
import marisa_trie
from collections import defaultdict


class EntityFinder:

    def __init__(self):
        self.entity_tries = {}

    def setup_entity_values(self, entities):
        for entity_name, entity_values in entities.items():
            self.entity_tries[entity_name] = marisa_trie.Trie(entity_values)

    def replace_entity_values(self, conversation):
        words = conversation.split()
        corrected_words = []
        values = defaultdict(list)

        for word in words:
            matches = {}
            for entity_name, entity_trie in self.entity_tries.items():
                if word in entity_trie:
                    matches[entity_name] = word

            if len(matches) == 0:
                corrected_words.append(word)
            elif len(matches) == 1:
                n, v = matches.popitem()
                corrected_words.append('@' + n)
                values[n].append(v)
            else:
                # What is the correct way to handle duplicates?
                corrected_words.append(word)

        # Construct return string
        output_text = ' '
        output_text = output_text.join(corrected_words)
        return output_text, values
