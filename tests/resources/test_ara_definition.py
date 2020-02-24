import json
from uuid import UUID, uuid4

import pytest
from citrine.exceptions import ModuleRegistrationFailedException
from taurus.entity.link_by_uid import LinkByUID

from citrine.ara.columns import MeanColumn, OriginalUnitsColumn, StdDevColumn, IdentityColumn
from citrine.ara.rows import MaterialRunByTemplate
from citrine.ara.variables import AttributeByTemplate, RootInfo
from citrine.resources.ara_definition import AraDefinitionCollection, AraDefinition
from tests.utils.factories import AraDefinitionFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> AraDefinitionCollection:
    return AraDefinitionCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def ara_definition() -> AraDefinition:
    def _ara_definition():
        return AraDefinition.build(AraDefinitionFactory())
    return _ara_definition


def empty_defn() -> AraDefinition:
    return AraDefinition(name="empty", description="empty",
                         datasets=[], rows=[], variables=[], columns=[])


def test_get_ara_definition_metadata(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    session.set_response(ara_definition)

    # When
    retrieved_ara_definition: AraDefinition = collection.get_with_version(ara_definition["definition_id"], ara_definition["version_number"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="GET",
        path="projects/{}/ara-definitions/{}/versions/{}".format(project_id, ara_definition["definition_id"], ara_definition["version_number"])
    )
    assert session.last_call == expect_call
    assert str(retrieved_ara_definition.definition_uid) == ara_definition["definition_id"]
    assert retrieved_ara_definition.version_number == ara_definition["version_number"]


def test_init_ara_definition():
    ara_definition = AraDefinition(name="foo", description="bar", rows=[], columns=[], variables=[], datasets=[])
    assert ara_definition.definition_uid is None
    assert ara_definition.version_number is None


def test_dup_names():
    """Make sure that variable name and headers are unique across an ara definition"""
    with pytest.raises(ValueError) as excinfo:
        AraDefinition(
            name="foo", description="bar", datasets=[], rows=[], columns=[],
            variables=[
                RootInfo(name="foo", headers=["foo", "bar"], field="name"),
                RootInfo(name="foo", headers=["foo", "baz"], field="name")
            ]
        )
    assert "Multiple" in str(excinfo.value)
    assert "foo" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        AraDefinition(
            name="foo", description="bar", datasets=[], rows=[], columns=[],
            variables=[
                RootInfo(name="foo", headers=["spam", "eggs"], field="name"),
                RootInfo(name="bar", headers=["spam", "eggs"], field="name")
            ]
        )
    assert "Multiple" in str(excinfo.value)
    assert "spam" in str(excinfo.value)


def test_missing_variable():
    """Make sure that every data_source matches a name of a variable"""
    with pytest.raises(ValueError) as excinfo:
        AraDefinition(
            name="foo", description="bar", datasets=[], rows=[], variables=[],
            columns=[
                MeanColumn(data_source="density")
            ]
        )
    assert "must match" in str(excinfo.value)
    assert "density" in str(excinfo.value)


def test_dump_example():
    density = AttributeByTemplate(
        name="density",
        headers=["Slice", "Density"],
        template=LinkByUID(scope="templates", id="density")
    )
    ara_definition = AraDefinition(
        name="Example Table",
        description="Illustrative example that's meant to show how Ara Definitions will look serialized",
        datasets=[uuid4()],
        variables=[density],
        rows=[MaterialRunByTemplate(templates=[LinkByUID(scope="templates", id="slices")])],
        columns=[
            MeanColumn(data_source=density.name),
            StdDevColumn(data_source=density.name),
            OriginalUnitsColumn(data_source=density.name),
        ]
    )
    print(json.dumps(ara_definition.dump(), indent=2))


def test_preview(collection, session):
    """Test that preview hits the right route"""
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'

    # When
    collection.preview(empty_defn(), [])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="projects/{}/ara-definitions/preview".format(project_id),
        json={"definition": empty_defn().dump(), "rows": []}
    )
    assert session.last_call == expect_call


def test_add_columns():
    """Test the behavior of AraDefinition.add_columns"""
    empty = empty_defn()

    # Check the mismatched name error
    with pytest.raises(ValueError) as excinfo:
        empty.add_columns(
            variable=RootInfo(name="foo", headers=["bar"], field="name"),
            columns=[IdentityColumn(data_source="bar")]
        )
    assert "data_source must be" in str(excinfo.value)

    # Check desired behavior
    with_name_col = empty.add_columns(
        variable=RootInfo(name="name", headers=["bar"], field="name"),
        columns=[IdentityColumn(data_source="name")]
    )
    assert with_name_col.variables == [RootInfo(name="name", headers=["bar"], field="name")]
    assert with_name_col.columns == [IdentityColumn(data_source="name")]

    # Check duplicate variable name error
    with pytest.raises(ValueError) as excinfo:
        with_name_col.add_columns(
            variable=RootInfo(name="name", headers=["bar"], field="name"),
            columns=[IdentityColumn(data_source="name")]
        )
    assert "already used" in str(excinfo.value)


def test_register_new(collection, session):
    """Test the behavior of AraDefinitionCollection.register() on an unregistered AraDefinition"""
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    ara_definition["definition_id"] = None
    ara_definition["id"] = None
    ara_definition["version_number"] = None
    session.set_response({"version": ara_definition})

    # When
    collection.register(collection.build(ara_definition))

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="POST",
        path="projects/{}/ara-definitions".format(project_id),
        json={"definition": collection.build(ara_definition).dump()}
    )
    assert session.last_call == expect_call


def test_register_existing(collection, session):
    """Test the behavior of AraDefinitionCollection.register() on a registered AraDefinition"""
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    definition_uid = ara_definition["definition_id"]
    assert definition_uid is not None
    session.set_response({"version": ara_definition})

    # When
    collection.register(collection.build(ara_definition))

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="PUT",
        path="projects/{}/ara-definitions/{}".format(project_id, definition_uid),
        json={"definition": collection.build(ara_definition).dump()}
    )
    assert session.last_call == expect_call


def test_update(collection, session):
    """Test the behavior of AraDefinitionCollection.update() on a registered AraDefinition"""
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    definition_uid = ara_definition["definition_id"]
    assert definition_uid is not None
    session.set_response({"version": ara_definition})

    # When
    collection.update(collection.build(ara_definition))

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="PUT",
        path="projects/{}/ara-definitions/{}".format(project_id, definition_uid),
        json={"definition": collection.build(ara_definition).dump()}
    )
    assert session.last_call == expect_call


def test_update_unregistered_fail(collection, session):
    """Test that AraDefinitionCollection.update() fails on an unregistered AraDefinition"""
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    ara_definition["definition_id"] = None
    ara_definition["id"] = None
    ara_definition["version_number"] = None
    session.set_response({"version": ara_definition})

    # When
    with pytest.raises(ValueError, match="Cannot update Ara Definition without a definition_uid."):
        collection.update(collection.build(ara_definition))
