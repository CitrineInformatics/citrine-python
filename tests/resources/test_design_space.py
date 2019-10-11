import uuid

from citrine.resources.design_space import DesignSpaceCollection


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
