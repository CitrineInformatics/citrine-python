"""Tests for Schema classes."""

from citrine.informatics.predictors import Predictor


def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def module_serialization_check(data, moduleClass):
    """Assert that given json is unchanged under round-robin (de)serialization.

    Parameters
    ----------
    data: json of a serialized module
    moduleClass: the appropriate class to deserialize the data
    """
    module = moduleClass.build(data)
    serialized = module.dump()
    serialized['id'] = data['id']
    assert serialized == valid_serialization_output(data)

def predictor_serialization_check(json, moduleClass):
    module = moduleClass.build(json)
    serialized = module.dump()
    assert serialized == dict(json["data"].items())
