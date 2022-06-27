import uuid
from copy import deepcopy
from random import random

import mock
import pytest

from citrine.exceptions import NotFound
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.design_spaces import EnumeratedDesignSpace, DesignSpace, ProductDesignSpace
from citrine.resources.design_space import DesignSpaceCollection
from tests.utils.session import FakeCall, FakeRequestResponse, FakeSession

@pytest.fixture
def valid_product_design_space(valid_product_design_space_data) -> ProductDesignSpace:
    data = deepcopy(valid_product_design_space_data)
    return DesignSpace.build(data)


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
                'descriptor': {
                    'type': 'RealDescriptor',
                    'descriptor_key': 'foo',
                    'lower_bound': 0.0,
                    'upper_bound': 1.0,
                    'units': ""
                },
                'lower_bound': 0.0,
                'upper_bound': 1.0,
            }],
        },
        'status': '',
    }

    # When
    design_space = collection.build(design_space_data)

    # Then
    assert design_space.uid == design_space_id
    assert design_space.name == 'My Design Space'
    assert design_space.dimensions[0].descriptor.key == 'foo'


def test_formulation_build(valid_formulation_design_space_data):
    pc = DesignSpaceCollection(uuid.uuid4(), None)
    design_space = pc.build(valid_formulation_design_space_data)
    assert design_space.archived
    assert design_space.name == 'formulation design space'
    assert design_space.description == 'formulates some things'
    assert design_space.formulation_descriptor.key == 'formulation'
    assert design_space.ingredients == {'foo'}
    assert design_space.labels == {'bar': {'foo'}}
    assert len(design_space.constraints) == 1
    assert design_space.resolution == 0.1


def test_design_space_limits():
    """Test that the validation logic is triggered before post/put-ing enumerated design spaces."""
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)

    too_big = EnumeratedDesignSpace(
        "foo",
        description="bar",
        descriptors=[RealDescriptor("R-{}".format(i), lower_bound=0, upper_bound=1, units="") for i in range(128)],
        data=[{"R-{}".format(i): random() for i in range(128)} for _ in range(2001)]
    )

    just_right = EnumeratedDesignSpace(
        "foo",
        description="bar",
        descriptors=[RealDescriptor("R-{}".format(i), lower_bound=0, upper_bound=1, units="") for i in range(128)],
        data=[{"R-{}".format(i): random() for i in range(128)} for _ in range(2000)]
    )

    # create mock post response by setting the status
    mock_response = just_right.dump()
    mock_response["status"] = "READY"
    session.responses.append(mock_response)

    # Then
    with pytest.raises(ValueError) as excinfo:
        collection.register(too_big)
    assert "only supports" in str(excinfo.value)

    # test register
    collection.register(just_right)

    # add back the response for the next test
    session.responses.append(mock_response)

    # test update
    collection.update(just_right)


def test_create_default(valid_product_design_space_data,
                        valid_product_design_space):
    # The instance field isn't renamed to config in objects returned from this route
    # This renames the config key to instance to match the data we get from the API
    data_with_instance = deepcopy(valid_product_design_space_data)
    data_with_instance['instance'] = data_with_instance.pop('config')

    session = FakeSession()
    session.set_response(data_with_instance)
    
    predictor_id = uuid.uuid4()
    collection = DesignSpaceCollection(
        project_id=uuid.uuid4(),
        session=session
    )

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces/default",
        json={
            "predictor_id": predictor_id,
            "include_ingredient_fraction_constraints": False,
            "include_label_fraction_constraints": False,
            "include_label_count_constraints": False
        },
        version="v2"
    )
    
    default_design_space = collection.create_default(predictor_id=predictor_id)

    assert session.num_calls == 1
    assert session.last_call == expected_call
    
    assert default_design_space.dump() == valid_product_design_space.dump()


@pytest.mark.parametrize("ingredient_fractions", (True, False))
@pytest.mark.parametrize("label_fractions", (True, False))
@pytest.mark.parametrize("label_count", (True, False))
def test_create_default_with_config(valid_product_design_space_data, valid_product_design_space,
                                    ingredient_fractions, label_fractions, label_count):
    # The instance field isn't renamed to config in objects returned from this route
    # This renames the config key to instance to match the data we get from the API
    data_with_instance = deepcopy(valid_product_design_space_data)
    data_with_instance['instance'] = data_with_instance.pop('config')

    session = FakeSession()
    session.set_response(data_with_instance)
    
    predictor_id = uuid.uuid4()
    collection = DesignSpaceCollection(
        project_id=uuid.uuid4(),
        session=session
    )

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces/default",
        json={
            "predictor_id": predictor_id,
            "include_ingredient_fraction_constraints": ingredient_fractions,
            "include_label_fraction_constraints": label_fractions,
            "include_label_count_constraints": label_count
        },
        version="v2"
    )
    
    default_design_space = collection.create_default(
        predictor_id=predictor_id,
        include_ingredient_fraction_constraints=ingredient_fractions,
        include_label_fraction_constraints=label_fractions,
        include_label_count_constraints=label_count
    )

    assert session.num_calls == 1
    assert session.last_call == expected_call
    
    assert default_design_space.dump() == valid_product_design_space.dump()


def test_list_design_spaces(valid_formulation_design_space_data, valid_enumerated_design_space_data):
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)
    session.set_response(
        {
            'entries': [valid_formulation_design_space_data, valid_enumerated_design_space_data],
            'next': ''
        }
    )

    # When
    design_spaces = list(collection.list(per_page=20))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/modules'.format(collection.project_id),
            params={'per_page': 20, 'module_type': "DESIGN_SPACE"})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(design_spaces) == 2


def test_experimental_deprecated(valid_formulation_design_space_data):
    # Given
    session = FakeSession()
    response = deepcopy(valid_formulation_design_space_data)
    response["experimental"] = True
    response["experimental_reasons"] = ["This is a test", "Of experimental reasons"]

    session.set_response(response)

    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    design_space = DesignSpace.build(valid_formulation_design_space_data)

    # When
    registered = dsc.register(design_space)

    # Then
    with pytest.deprecated_call():
        assert registered.experimental is False
    with pytest.deprecated_call():
        assert registered.experimental_reasons == []


def test_archive(valid_formulation_design_space_data):
    session = FakeSession()
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    base_path = DesignSpaceCollection._path_template.format(project_id=dsc.project_id)
    ds_id = valid_formulation_design_space_data["id"]

    get_response = deepcopy(valid_formulation_design_space_data)
    update_response = {**get_response, "archived": True}
    session.set_responses(get_response, update_response)

    expected_payload = deepcopy(update_response)
    del expected_payload["status"]
    del expected_payload["status_info"]
    del expected_payload["id"]

    archived_design_space = dsc.archive(ds_id)

    assert archived_design_space.archived
    assert session.calls == [
        FakeCall(method='GET', path=f"{base_path}/{ds_id}"),
        FakeCall(method='PUT', path=f"{base_path}/{ds_id}", json=expected_payload)
    ]

def test_restore(valid_formulation_design_space_data):
    session = FakeSession()
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    base_path = DesignSpaceCollection._path_template.format(project_id=dsc.project_id)
    ds_id = valid_formulation_design_space_data["id"]

    get_response = deepcopy(valid_formulation_design_space_data)
    update_response = {**get_response, "archived": False}
    session.set_responses(get_response, update_response)

    expected_payload = deepcopy(update_response)
    del expected_payload["status"]
    del expected_payload["status_info"]
    del expected_payload["id"]

    archived_design_space = dsc.restore(ds_id)

    assert not archived_design_space.archived
    assert session.calls == [
        FakeCall(method='GET', path=f"{base_path}/{ds_id}"),
        FakeCall(method='PUT', path=f"{base_path}/{ds_id}", json=expected_payload)
    ]

def test_archive_restore_not_found():
    session = FakeSession()
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    base_path = DesignSpaceCollection._path_template.format(project_id=dsc.project_id)

    response = FakeRequestResponse(404)
    response.request.method = "GET"
    session.set_response(NotFound(base_path, response))

    with pytest.raises(RuntimeError):
        dsc.archive(uuid.uuid4())

    with pytest.raises(RuntimeError):
        dsc.restore(uuid.uuid4())
