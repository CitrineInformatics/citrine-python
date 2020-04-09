import json
from uuid import UUID, uuid4

import pytest
from taurus.entity.link_by_uid import LinkByUID

from citrine.ara.columns import MeanColumn, OriginalUnitsColumn, StdDevColumn, IdentityColumn
from citrine.ara.rows import MaterialRunByTemplate
from citrine.ara.variables import AttributeByTemplate, RootInfo, IngredientQuantityDimension,\
    IngredientQuantityByProcessAndName, IngredientIdentifierByProcessTemplateAndName
from citrine.resources.ara_definition import AraDefinitionCollection, AraDefinition
from citrine.resources.project import Project
from citrine.resources.process_template import ProcessTemplate
from tests.utils.factories import AraDefinitionFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    project = Project(
        name="Test Ara project",
        session=session
    )
    project.uid = UUID('6b608f78-e341-422c-8076-35adc8828545')
    return project


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
    session.set_response({"version": ara_definition})

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


def test_add_all_ingredients(session, project):
    """Test the behavior of AraDefinition.add_all_ingredients."""
    # GIVEN
    process_id = '3a308f78-e341-f39c-8076-35a2c88292ad'
    process_name = 'mixing'
    allowed_names = ["gold nanoparticles", "methanol", "acetone"]
    process_link = LinkByUID('id', process_id)
    session.set_response(
        ProcessTemplate(process_name, uids={'id': process_id}, allowed_names=allowed_names).dump()
    )

    # WHEN we add all ingredients in a volume basis
    def1 = empty_defn().add_all_ingredients(process_template=process_link, project=project,
                                            quantity_dimension=IngredientQuantityDimension.VOLUME)
    # THEN there should be 2 variables and columns for each name, one for id and one for quantity
    assert len(def1.variables) == len(allowed_names) * 2
    assert len(def1.columns) == len(def1.variables)
    for name in allowed_names:
        assert next((var for var in def1.variables if name in var.headers
                     and isinstance(var, IngredientQuantityByProcessAndName)), None) is not None
        assert next((var for var in def1.variables if name in var.headers
                     and isinstance(var, IngredientIdentifierByProcessTemplateAndName)), None) is not None

    session.set_response(
        ProcessTemplate(process_name, uids={'id': process_id}, allowed_names=allowed_names).dump()
    )
    # WHEN we add all ingredients to the same Ara definition as absolute quantities
    def2 = def1.add_all_ingredients(process_template=process_link, project=project,
                                    quantity_dimension=IngredientQuantityDimension.ABSOLUTE)
    # THEN there should be 1 new variable for each name, corresponding to the quantity
    #   There is already a variable for id
    #   There should be 2 new columns for each name, one for the quantity and one for the units
    new_variables = def2.variables[len(def1.variables):]
    new_columns = def2.columns[len(def1.columns):]
    assert len(new_variables) == len(allowed_names)
    assert len(new_columns) == len(allowed_names) * 2
    for name in allowed_names:
        assert next((var for var in new_variables if name in var.headers
                     and isinstance(var, IngredientQuantityByProcessAndName)), None) is not None

    session.set_response(
        ProcessTemplate(process_name, uids={'id': process_id}, allowed_names=allowed_names).dump()
    )
    # WHEN we add all ingredients to the same Ara definition in a volume basis
    # THEN it raises an exception because these variables and columns already exist
    with pytest.raises(ValueError):
        def2.add_all_ingredients(process_template=process_link, project=project,
                                 quantity_dimension=IngredientQuantityDimension.VOLUME)

    # If the process template has an empty allowed_names list then an error should be raised
    session.set_response(
        ProcessTemplate(process_name, uids={'id': process_id}).dump()
    )
    with pytest.raises(RuntimeError):
        empty_defn().add_all_ingredients(process_template=process_link, project=project,
                                         quantity_dimension=IngredientQuantityDimension.VOLUME)


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
