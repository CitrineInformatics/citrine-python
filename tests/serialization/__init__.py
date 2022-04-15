"""Tests for Schema classes."""

from citrine.informatics.predictors import Predictor


def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def serialization_check(json, moduleClass):
    """Assert that given json is unchanged under round-robin (de)serialization.

    Parameters
    ----------
    json: json of a serialized module
    moduleClass: the appropriate class to deserialize the data
    """
    module = moduleClass.build(json)
    serialized = module.dump()
    if issubclass(moduleClass, Predictor):
        assert serialized == dict(json["data"].items())
    else:
        serialized['id'] = json['id']
        assert serialized == valid_serialization_output(json)
