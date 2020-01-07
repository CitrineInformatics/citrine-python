from uuid import UUID

import pytest

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


def test_get_ara_definition_metadata(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    ara_definition = AraDefinitionFactory()
    session.set_response(ara_definition)

    # When
    retrieved_ara_definition: AraDefinition = collection.get(ara_definition["id"], ara_definition["version"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="GET",
        path="projects/{}/ara_definitions/{}/versions/{}".format(project_id, ara_definition["id"], ara_definition["version"])
    )
    assert session.last_call == expect_call
    assert str(retrieved_ara_definition.uid) == ara_definition["id"]
    assert retrieved_ara_definition.version == ara_definition["version"]


def test_init_ara_definition():
    ara_definition = AraDefinition(name="foo", description="bar", rows=[], columns=[], variables=[], datasets=[])
    assert ara_definition.uid is None
    assert ara_definition.version is None
