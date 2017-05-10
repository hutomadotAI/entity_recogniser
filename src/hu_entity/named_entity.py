import json

class NamedEntity(object):
    """
    Class holding the basic entity defintion
    """
    def __init__(self, named_entity, label):
        self.named_entity = named_entity
        self.label = label

    def to_json(self):
        """Convert self to JSON string"""
        data = {'named_entity': self.named_entity,
                'lable': self.label}
        json_data = json.dumps(data)
        return json_data

