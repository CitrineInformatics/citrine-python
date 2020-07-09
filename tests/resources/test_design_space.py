import uuid
from random import random

import pytest

from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.resources.design_space import DesignSpaceCollection
from tests.utils.session import FakeSession


def test_design_space_build():
    # Given
    collection = DesignSpaceCollection(uuid.uuid4(), None)
    design_space_id = uuid.uuid4()

    # TODO:  At some point we should create data factories for this
    design_space_data = {
        'id': str(design_space_id),
        'config': {
            'type': 'Univariate',
            'name': 'My Design Space',
            'description': 'For testing',
            'dimensions': [{
                'type': 'ContinuousDimension',
                'template_id': str(uuid.uuid4()),
                'descriptor': {
                    'type': 'RealDescriptor',
                    'descriptor_key': 'foo',
                    'lower_bound': 0.0,
                    'upper_bound': 1.0,
                },
                'lower_bound': 0.0,
                'upper_bound': 1.0,
            }],
        },
        'status': '',
        'schema_id': '6c16d694-d015-42a7-b462-8ef299473c9a',
    }

    # When
    design_space = collection.build(design_space_data)

    # Then
    assert design_space.uid == design_space_id
    assert design_space.name == 'My Design Space'
    assert design_space.dimensions[0].descriptor.key == 'foo'


def test_design_space_limits():
    """Test that the validation logic is triggered before post/put-ing enumerated design spaces."""
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)

    too_long = EnumeratedDesignSpace(
        "foo",
        "bar",
        descriptors=[RealDescriptor("x", 0, 1)],
        data=[{"x": random()} for _ in range(2001)]
    )

    too_wide = EnumeratedDesignSpace(
        "foo",
        "bar",
        descriptors=[RealDescriptor("R-{}".format(i), 0, 1) for i in range(129)],
        data=[]
    )

    just_right = EnumeratedDesignSpace(
        "foo",
        "bar",
        descriptors=[RealDescriptor("R-{}".format(i), 0, 1) for i in range(10)],
        data=[{"R-{}".format(i): random() for i in range(128)} for _ in range(1000)]
    )

    # create mock post response by setting the status
    mock_response = just_right.dump()
    session.responses.append(mock_response)

    # Then
    with pytest.raises(ValueError) as excinfo:
        collection.register(too_long)
    assert "only supports" in str(excinfo.value)

    with pytest.raises(ValueError):
        collection.update(too_wide)
    assert "only supports" in str(excinfo.value)

    # test register
    collection.register(just_right)

    # add back the response for the next test
    session.responses.append(mock_response)

    # test update
    collection.update(just_right)
