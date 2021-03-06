"""Tests for Schema classes."""


def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def serialization_check(data, moduleClass):
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
