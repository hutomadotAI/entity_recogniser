import json

class NamedEntity(object):
    """
    Class holding the basic entity defintion
    """
    def __init__(self, named_entity, label, start_loc, end_loc):
        self.named_entity = named_entity
        self.label = label
        self.start_loc = start_loc
        self.end_loc = end_loc

    def __repr__(self):
        """String representation of our objects"""
        obj_str = "NamedEntity({}, {}, {}, {})".format(
            self.named_entity, self.label, self.start_loc, self.end_loc)
        return obj_str


class CustomJsonEncoder(json.JSONEncoder):
    """Custom Json Encoder for our custom objects"""
    def default(self, obj):
        if isinstance(obj, NamedEntity):
            return {'named_entity': obj.named_entity,
                'label': obj.label, 'start': obj.start_loc, 'end': obj.end_loc}
        return json.JSONEncoder.default(self, obj)

def dumps_custom(source_object):
    """Custom version of dumps that understands our Custom objects"""
    json_out = json.dumps(source_object, cls=CustomJsonEncoder)
    return json_out
