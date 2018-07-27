import json
import marisa_trie


class EntityFinder:

    def __init__(self):
        self.entity_tries = {}

    def setup_entity_values(self, entities):
        for entity in entities:
            for entity_name, entity_values in entity.items():
                self.entity_tries[entity_name] = marisa_trie.Trie(entity_values)

    def replace_entity_values(self, conversation):
        words = conversation.split()
        corrected_words = []

        for word in words:
            matches = []
            for entity_name, entity_trie in self.entity_tries.items():
                if word in entity_trie:
                    matches.append(entity_name)

            if len(matches) == 0:
                corrected_words.append(word)
            elif len(matches) == 1:
                corrected_words.append('@' + matches[0])
            else:
                # What is the
                corrected_words.append(word)

        # Construct return string
        output_text = ' '
        output_text = output_text.join(corrected_words)
        return output_text
