"""Tests for Schema classes."""


def valid_serialization_output(valid_data):
    exclude_fields = ['status', 'status_detail']
    return {x: y for x, y in valid_data.items() if x not in exclude_fields}


def design_space_serialization_check(data, moduleClass):
    """Assert that given json is unchanged under round-robin (de)serialization.

    Parameters
    ----------
    data: json of a serialized module
    moduleClass: the appropriate class to deserialize the data
    """
    module = moduleClass.build(data)
    serialized = module.dump()
    assert serialized == valid_serialization_output(data)['data']


def predictor_serialization_check(json, module_class):
    module = module_class.build(json)
    serialized = module.dump()
    assert serialized == dict(json["data"].items())


def predictor_node_serialization_check(json, module_class):
    module = module_class.build(json)
    serialized = module.dump()
    assert serialized == dict(json.items())
