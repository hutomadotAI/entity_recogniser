import json

# map from typeshttps://spacy.io/docs/usage/entity-recognition#entity-type
ENTITY_CATEGORY_MAPPING = {
    # names of entities
    "GPE": "sys.places",
    "PERSON": "sys.person",
    "NORP": "sys.group",
    "FAC": "sys.places",
    "ORG": "sys.organization",
    "LOC": "sys.places",
    "LANGUAGE": "sys.group",
    # values recognized
    "DATE": "sys.date",
    "TIME": "sys.time",
    "PERCENT": "sys.percent",
    "MONEY": "sys.number",
    "QUANTITY": "sys.number",
    "ORDINAL": "sys.ordinal",
    "CARDINAL": "sys.number",
    # custom entities we added
    "custom_cities": "sys.places",
}


class NamedEntity(object):
    """
    Class holding the basic entity defintion
    """

    def __init__(self, entity_value, spacy_category, start_loc, end_loc):
        self.entity_value = entity_value
        self.spacy_category = spacy_category
        self.category = ENTITY_CATEGORY_MAPPING.get(spacy_category, None)
        self.start_loc = start_loc
        self.end_loc = end_loc

    def __repr__(self):
        """String representation of our objects"""
        obj_str = "({}, {}=>{}, {}, {})".format(
            self.entity_value, self.spacy_category, self.category,
            self.start_loc, self.end_loc)
        return obj_str


class CustomJsonEncoder(json.JSONEncoder):
    """Custom Json Encoder for our custom objects"""

    def default(self, obj):
        if isinstance(obj, NamedEntity):
            return {
                'value': obj.entity_value,
                'category': obj.category,
                'start': obj.start_loc,
                'end': obj.end_loc
            }
        return json.JSONEncoder.default(self, obj)


def dumps_custom(source_object):
    """Custom version of dumps that understands our Custom objects"""
    json_out = json.dumps(source_object, cls=CustomJsonEncoder)
    return json_out
