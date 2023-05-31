import pytest
import uuid

from citrine.informatics.design_spaces.design_space import SampleDesignSpaceInput
from citrine.informatics.executions.sample_design_space_execution import SampleDesignSpaceExecution
from citrine.resources.sample_design_space_execution import SampleDesignSpaceExecutionCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> SampleDesignSpaceExecutionCollection:
    return SampleDesignSpaceExecutionCollection(
        project_id=uuid.uuid4(),
        design_space_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def sample_design_space_execution(collection: SampleDesignSpaceExecutionCollection, sample_design_space_execution_dict) -> SampleDesignSpaceExecution:
    return collection.build(sample_design_space_execution_dict)


def test_basic_methods(sample_design_space_execution, collection):
    assert "SampleDesignSpaceExecution" in str(sample_design_space_execution)

    with pytest.raises(NotImplementedError):
        collection.register(sample_design_space_execution)

    with pytest.raises(NotImplementedError):
        collection.update(sample_design_space_execution)


def test_build_new_execution(collection, sample_design_space_execution_dict):
    execution: SampleDesignSpaceExecution = collection.build(sample_design_space_execution_dict)

    assert str(execution.uid) == sample_design_space_execution_dict["id"]
    assert execution.project_id == collection.project_id
    assert execution._session == collection.session
    assert execution.in_progress() and not execution.succeeded() and not execution.failed()


def test_trigger_execution(collection: SampleDesignSpaceExecutionCollection, sample_design_space_execution_dict, session):
    # Given
    session.set_response(sample_design_space_execution_dict)
    sample_design_space_execution_input = SampleDesignSpaceInput(
        n_candidates=10
    )

    # When
    actual_execution = collection.trigger(sample_design_space_execution_input)

    # Then
    assert str(actual_execution.uid) == sample_design_space_execution_dict["id"]
    expected_path = '/projects/{}/design-spaces/{}/sample'.format(
        collection.project_id, collection.design_space_id
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json={
            'n_candidates': sample_design_space_execution_input.n_candidates,
        }
    )


def test_sample_design_space_execution_results(sample_design_space_execution: SampleDesignSpaceExecution, session, example_sample_design_space_response):
    # Given
    session.set_response(example_sample_design_space_response)

    # When
    list(sample_design_space_execution.results(per_page=4))

    # Then
    expected_path = '/projects/{}/design-spaces/{}/sample/{}/results'.format(
        sample_design_space_execution.project_id,
        sample_design_space_execution.design_space_id,
        sample_design_space_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path, params={"page": 1, "per_page": 4})


def test_sample_design_space_execution_result(sample_design_space_execution: SampleDesignSpaceExecution, session, example_sample_design_space_response):
    # Given
    session.set_response(example_sample_design_space_response["response"][0])

    # When
    result_id=example_sample_design_space_response["response"][0]["id"]
    sample_design_space_execution.result(result_id=result_id)

    # Then
    expected_path = '/projects/{}/design-spaces/{}/sample/{}/results/{}'.format(
        sample_design_space_execution.project_id,
        sample_design_space_execution.design_space_id,
        sample_design_space_execution.uid,
        result_id,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path)


def test_list(collection: SampleDesignSpaceExecutionCollection, session):
    session.set_response({"page": 1, "per_page": 4, "next": "", "response": []})
    lst = list(collection.list(per_page=4))
    assert len(lst) == 0

    expected_path = '/projects/{}/design-spaces/{}/sample'.format(
        collection.project_id,
        collection.design_space_id,
    )
    assert session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={"page": 1, "per_page": 4}
    )


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())