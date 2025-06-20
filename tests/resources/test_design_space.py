import random
import uuid
from copy import deepcopy
from datetime import datetime, timezone

import mock
import pytest

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.descriptors import RealDescriptor, FormulationKey
from citrine.informatics.design_spaces import DefaultDesignSpaceMode, DesignSpace, \
        DesignSpaceSettings, EnumeratedDesignSpace, HierarchicalDesignSpace, ProductDesignSpace
from citrine.resources.design_space import DesignSpaceCollection
from citrine.resources.status_detail import StatusDetail, StatusLevelEnum
from tests.utils.session import FakeCall, FakeSession

def _ds_dict_to_response(ds_dict, status="CREATED"):
    time = '2020-04-23T15:46:26Z'
    return {
        "id": str(uuid.uuid4()),
        "data": {
            "name": ds_dict["name"],
            "description": ds_dict["description"],
            "instance": ds_dict
        },
        "metadata": {
            "created": {
                "user": str(uuid.uuid4()),
                "time": time
            },
            "updated": {
                "user": str(uuid.uuid4()),
                "time": time
            },
            "status": {
                "name": status,
                "detail": []
            }
        }
    }

def _ds_to_response(ds, status="CREATED"):
    return _ds_dict_to_response(ds.dump()["instance"], status)


@pytest.fixture
def valid_product_design_space(valid_product_design_space_data) -> ProductDesignSpace:
    data = deepcopy(valid_product_design_space_data)
    return DesignSpace.build(data)


def test_design_space_build(valid_product_design_space_data):
    # Given
    collection = DesignSpaceCollection(uuid.uuid4(), None)
    design_space_id = valid_product_design_space_data["id"]

    # When
    design_space = collection.build(valid_product_design_space_data)

    # Then
    assert str(design_space.uid) == design_space_id
    assert design_space.name == valid_product_design_space_data["data"]["instance"]["name"]
    assert design_space.dimensions[0].descriptor.key == valid_product_design_space_data["data"]["instance"]["dimensions"][0]["descriptor"]["descriptor_key"]


def test_design_space_build_with_status_detail(valid_product_design_space_data):
    # Given
    collection = DesignSpaceCollection(uuid.uuid4(), None)

    status_detail_data = {("Info", "info_msg"), ("Warning", "warning msg"), ("Error", "error msg")}
    data = deepcopy(valid_product_design_space_data)
    data["metadata"]["status"]["detail"] = [{"level": level, "msg": msg} for level, msg in status_detail_data]

    # When
    design_space = collection.build(data)

    # Then
    status_detail_tuples = {(detail.level, detail.msg) for detail in design_space.status_detail}
    assert status_detail_tuples == status_detail_data


def test_formulation_build(valid_formulation_design_space_data):
    pc = DesignSpaceCollection(uuid.uuid4(), None)
    design_space = pc.build(valid_formulation_design_space_data)
    assert design_space.name == 'formulation design space'
    assert design_space.description == 'formulates some things'
    assert design_space.formulation_descriptor.key == FormulationKey.HIERARCHICAL.value
    assert design_space.ingredients == {'foo'}
    assert design_space.labels == {'bar': {'foo'}}
    assert len(design_space.constraints) == 1
    assert design_space.resolution == 0.1


def test_hierarchical_build(valid_hierarchical_design_space_data):
    dc = DesignSpaceCollection(uuid.uuid4(), None)
    hds = dc.build(valid_hierarchical_design_space_data)
    assert hds.name == 'hierarchical design space'
    assert hds.description == 'does things but in levels'
    assert hds.root.formulation_subspace is not None
    assert hds.root.template_link is not None
    assert hds.root.display_name is not None
    assert len(hds.root.attributes) == 2
    assert len(hds.subspaces) == 1


def test_convert_to_hierarchical(valid_hierarchical_design_space_data):
    data_payload = valid_hierarchical_design_space_data["data"]

    session = FakeSession()
    session.set_response(data_payload)

    dc = DesignSpaceCollection(uuid.uuid4(), session)

    ds_id = uuid.uuid4()
    predictor_id = uuid.uuid4()
    dc.convert_to_hierarchical(uid=ds_id, predictor_id=predictor_id, predictor_version=2)

    expected_payload = {
        "predictor_id": str(predictor_id),
        "predictor_version": 2
    }
    expected_call = FakeCall(
        method='POST',
        path=f"projects/{dc.project_id}/design-spaces/{ds_id}/convert-hierarchical",
        json=expected_payload,
        version="v3"
    )

    assert session.num_calls == 1
    assert session.last_call == expected_call


def test_design_space_limits():
    """Test that the validation logic is triggered before post/put-ing enumerated design spaces."""
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)
        
    descriptors = [RealDescriptor(f"R-{i}", lower_bound=0, upper_bound=1, units="") for i in range(128)]
    descriptor_values = {f"R-{i}": str(random.random()) for i in range(128)}

    just_right = EnumeratedDesignSpace(
        "just right",
        description="just right desc",
        descriptors=descriptors,
        data=[descriptor_values] * 2000
    )

    too_big = EnumeratedDesignSpace(
        "too big",
        description="too big desc",
        descriptors=just_right.descriptors,
        data=[descriptor_values] * 2001
    )

    # create mock post response by setting the status.
    # Deserializing that huge dict takes a long time, and it's done twice when making a call to
    # register or update (the second is the automatic validation kick-off). Since we're only
    # interested in checking the validation pre-request, we can specify a tiny response to speed up
    # the test execution.
    dummy_desc = descriptors[0]
    dummy_resp = EnumeratedDesignSpace(
        "basic",
        description="basic desc",
        descriptors=[dummy_desc],
        data=[{dummy_desc.key: descriptor_values[dummy_desc.key]}]
    )
    mock_response = _ds_to_response(dummy_resp, status="READY")
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


@pytest.mark.parametrize("predictor_version", (2, "1", "latest", None))
def test_create_default(predictor_version, valid_product_design_space):
    session = FakeSession()
    session.set_response(valid_product_design_space.dump())
   
    predictor_id = uuid.uuid4()
    collection = DesignSpaceCollection(
        project_id=uuid.uuid4(),
        session=session
    )

    expected_payload = DesignSpaceSettings(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_ingredient_fraction_constraints=False,
        include_label_fraction_constraints=False,
        include_label_count_constraints=False,
        include_parameter_constraints=False,
        mode=DefaultDesignSpaceMode.ATTRIBUTE
    ).dump()

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces/default",
        json=expected_payload,
        version="v3"
    )

    default_design_space = collection.create_default(predictor_id=predictor_id, predictor_version=predictor_version)

    assert session.num_calls == 1
    assert session.last_call == expected_call
    
    expected_response = {**valid_product_design_space.dump(), "settings": expected_payload}
    assert default_design_space.dump() == expected_response


@pytest.mark.parametrize("predictor_version", (2, "1", "latest", None))
def test_create_default_hierarchical(predictor_version, valid_hierarchical_design_space_data):
    valid_hierarchical_design_space = HierarchicalDesignSpace.build(valid_hierarchical_design_space_data)

    session = FakeSession()
    session.set_response(valid_hierarchical_design_space.dump())
   
    predictor_id = uuid.uuid4()
    collection = DesignSpaceCollection(
        project_id=uuid.uuid4(),
        session=session
    )

    expected_payload = DesignSpaceSettings(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_ingredient_fraction_constraints=False,
        include_label_fraction_constraints=False,
        include_label_count_constraints=False,
        include_parameter_constraints=False,
        mode=DefaultDesignSpaceMode.HIERARCHICAL
    ).dump()

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces/default",
        json=expected_payload,
        version="v3"
    )

    default_design_space = collection.create_default(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        mode=DefaultDesignSpaceMode.HIERARCHICAL
    )

    assert session.num_calls == 1
    assert session.last_call == expected_call
    
    expected_response = {**valid_hierarchical_design_space.dump(), "settings": expected_payload}
    assert default_design_space.dump() == expected_response


@pytest.mark.parametrize("ingredient_fractions", (True, False))
@pytest.mark.parametrize("label_fractions", (True, False))
@pytest.mark.parametrize("label_count", (True, False))
@pytest.mark.parametrize("parameters", (True, False))
def test_create_default_with_config(valid_product_design_space, ingredient_fractions,
                                    label_fractions, label_count, parameters):
    session = FakeSession()
    session.set_response(valid_product_design_space.dump())
    
    predictor_id = uuid.uuid4()
    predictor_version = random.randint(1, 10)
    collection = DesignSpaceCollection(
        project_id=uuid.uuid4(),
        session=session
    )
    
    expected_payload = DesignSpaceSettings(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_ingredient_fraction_constraints=ingredient_fractions,
        include_label_fraction_constraints=label_fractions,
        include_label_count_constraints=label_count,
        include_parameter_constraints=parameters,
        mode=DefaultDesignSpaceMode.ATTRIBUTE
    ).dump()

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces/default",
        json=expected_payload,
        version="v3"
    )

    default_design_space = collection.create_default(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_ingredient_fraction_constraints=ingredient_fractions,
        include_label_fraction_constraints=label_fractions,
        include_label_count_constraints=label_count,
        include_parameter_constraints=parameters
    )

    assert session.num_calls == 1
    assert session.last_call == expected_call
    
    expected_response = {**valid_product_design_space.dump(), "settings": expected_payload}
    assert default_design_space.dump() == expected_response


def test_list_design_spaces(valid_formulation_design_space_data, valid_enumerated_design_space_data):
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)
    session.set_response({
        'response': [valid_formulation_design_space_data, valid_enumerated_design_space_data]
    })

    # When
    design_spaces = list(collection.list(per_page=20))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/design-spaces'.format(collection.project_id),
            params={'per_page': 20, 'page': 1, 'archived': False})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(design_spaces) == 2


def test_list_all_design_spaces(valid_formulation_design_space_data, valid_enumerated_design_space_data):
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)
    session.set_response({
        'response': [valid_formulation_design_space_data, valid_enumerated_design_space_data]
    })

    # When
    design_spaces = list(collection.list_all(per_page=25))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/design-spaces'.format(collection.project_id),
            params={'per_page': 25, 'page': 1})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(design_spaces) == 2


def test_list_archived_design_spaces(valid_formulation_design_space_data, valid_enumerated_design_space_data):
    # Given
    session = FakeSession()
    collection = DesignSpaceCollection(uuid.uuid4(), session)
    session.set_response({
        'response': [valid_formulation_design_space_data, valid_enumerated_design_space_data]
    })

    # When
    design_spaces = list(collection.list_archived(per_page=25))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/design-spaces'.format(collection.project_id),
            params={'per_page': 25, 'page': 1, 'archived': True})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(design_spaces) == 2


def test_archive(valid_formulation_design_space_data):
    session = FakeSession()
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    base_path = DesignSpaceCollection._path_template.format(project_id=dsc.project_id)
    ds_id = valid_formulation_design_space_data["id"]

    response = deepcopy(valid_formulation_design_space_data)
    response["metadata"]["archived"] = response["metadata"]["created"]
    session.set_response(response)

    archived_design_space = dsc.archive(ds_id)

    assert archived_design_space.is_archived
    assert session.calls == [
        FakeCall(method='PUT', path=f"{base_path}/{ds_id}/archive", json={}),
    ]


def test_restore(valid_formulation_design_space_data):
    session = FakeSession()
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    base_path = DesignSpaceCollection._path_template.format(project_id=dsc.project_id)
    ds_id = valid_formulation_design_space_data["id"]

    response = deepcopy(valid_formulation_design_space_data)
    if "archived" in response["metadata"]:
        del response["metadata"]["archived"]
    session.set_response(deepcopy(response))

    restored_design_space = dsc.restore(ds_id)

    assert not restored_design_space.is_archived
    assert session.calls == [
        FakeCall(method='PUT', path=f"{base_path}/{ds_id}/restore", json={}),
    ]


def test_get_none():
    """Trying to get a design space with uid=None should result in an informative error."""
    dsc = DesignSpaceCollection(uuid.uuid4(), FakeSession())

    with pytest.raises(ValueError) as excinfo:
        dsc.get(uid=None)

    assert "uid=None" in str(excinfo.value)


def test_failed_register(valid_product_design_space_data):
    response_data = deepcopy(valid_product_design_space_data)
    response_data['metadata']['status']['name'] = 'INVALID'

    session = FakeSession()
    session.set_response(response_data)
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    ds = dsc.build(deepcopy(valid_product_design_space_data))
    
    retval = dsc.register(ds)
    
    base_path = f"/projects/{dsc.project_id}/design-spaces"
    assert session.calls == [
        FakeCall(method='POST', path=base_path, json=ds.dump()),
    ]
    assert retval.dump() == ds.dump()


def test_failed_update(valid_product_design_space_data):
    response_data = deepcopy(valid_product_design_space_data)
    response_data['metadata']['status']['name'] = 'INVALID'

    session = FakeSession()
    session.set_response(response_data)
    dsc = DesignSpaceCollection(uuid.uuid4(), session)
    ds = dsc.build(deepcopy(valid_product_design_space_data))
    
    retval = dsc.update(ds)
    
    base_path = f"/projects/{dsc.project_id}/design-spaces"
    assert session.calls == [
        FakeCall(method='PUT', path=f'{base_path}/{ds.uid}', json=ds.dump()),
    ]
    assert retval.dump() == ds.dump()


def test_delete_not_supported():
    dsc = DesignSpaceCollection(uuid.uuid4(), FakeSession())
    with pytest.raises(NotImplementedError):
        dsc.delete(uuid.uuid4())


def test_carrying_settings_from_create_default(valid_product_design_space):
    predictor_id = uuid.uuid4()
    predictor_version = 4

    session = FakeSession()

    ds_resp = _ds_to_response(valid_product_design_space)
    session.set_responses(ds_resp["data"], deepcopy(ds_resp), deepcopy(ds_resp))

    collection = DesignSpaceCollection(project_id=uuid.uuid4(), session=session)

    default_design_space = collection.create_default(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_label_count_constraints=True
    )
    registered = collection.register(default_design_space)

    expected_settings = DesignSpaceSettings(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        include_ingredient_fraction_constraints=False,
        include_label_fraction_constraints=False,
        include_label_count_constraints=True,
        include_parameter_constraints=False,
        mode=DefaultDesignSpaceMode.ATTRIBUTE
    )
    expected_payload = {**valid_product_design_space.dump(), "settings": expected_settings.dump()}

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces",
        json=expected_payload,
        version="v3"
    )

    assert session.num_calls == 3
    assert session.calls[1] == expected_call


def test_carrying_settings_from_get(valid_product_design_space):
    predictor_id = uuid.uuid4()
    predictor_version = 4

    session = FakeSession()
    
    expected_settings = DesignSpaceSettings(
        predictor_id=predictor_id,
        predictor_version=predictor_version,
        exclude_intermediates=True,
        include_ingredient_fraction_constraints=False,
        include_label_fraction_constraints=False,
        include_label_count_constraints=False,
        include_parameter_constraints=True,
        mode=DefaultDesignSpaceMode.ATTRIBUTE
    )

    ds_resp = _ds_to_response(valid_product_design_space)
    ds_resp["metadata"]["settings"] = expected_settings.dump()
    session.set_responses(deepcopy(ds_resp), deepcopy(ds_resp), deepcopy(ds_resp))

    collection = DesignSpaceCollection(project_id=uuid.uuid4(), session=session)

    retrieved = collection.get(uuid.uuid4())
    registered = collection.register(retrieved)

    expected_payload = {**valid_product_design_space.dump(), "settings": expected_settings.dump()}

    expected_call = FakeCall(
        method='POST',
        path=f"projects/{collection.project_id}/design-spaces",
        json=expected_payload,
        version="v3"
    )

    assert session.num_calls == 3
    assert session.calls[1] == expected_call


def test_locked(valid_product_design_space_data):
    session = FakeSession()
    collection = DesignSpaceCollection(project_id=uuid.uuid4(), session=session)

    session.set_response(deepcopy(valid_product_design_space_data))

    ds = collection.get(uuid.uuid4())

    assert not ds.is_locked
    assert ds.locked_by is None
    assert ds.lock_time is None

    lock_user = uuid.uuid4()
    lock_time = datetime(2020, 4, 23, 15, 46, 23, tzinfo=timezone.utc)
    lock_timestamp = int(lock_time.timestamp()) * 1000

    response_data = deepcopy(valid_product_design_space_data)
    response_data['metadata']['locked'] = {'user': str(lock_user), 'time': lock_timestamp}

    session.set_response(response_data)

    ds = collection.get(uuid.uuid4())

    assert ds.is_locked
    assert ds.locked_by == lock_user
    assert ds.lock_time == lock_time
