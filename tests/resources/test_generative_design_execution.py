import pytest
import uuid

from citrine.informatics.design_candidate import GenerativeDesignExecutionInput
from citrine.informatics.executions.generative_design_execution import GenerativeDesignExecution
from citrine.resources.generative_design_execution import GenerativeDesignExecutionCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> GenerativeDesignExecutionCollection:
    return GenerativeDesignExecutionCollection(
        project_id=uuid.uuid4(),
        session=session,
    )


@pytest.fixture
def generative_design_execution(collection: GenerativeDesignExecutionCollection, generative_design_execution_dict) -> GenerativeDesignExecution:
    return collection.build(generative_design_execution_dict)


def test_basic_methods(generative_design_execution, collection):
    assert "GenerativeDesignExecution" in str(generative_design_execution)

    with pytest.raises(NotImplementedError):
        collection.register(generative_design_execution)

    with pytest.raises(NotImplementedError):
        collection.update(generative_design_execution)

    with pytest.raises(NotImplementedError):
        collection.archive(generative_design_execution)

    with pytest.raises(NotImplementedError):
        collection.restore(generative_design_execution)


def test_build_new_execution(collection, generative_design_execution_dict):
    # Given
    generative_design_execution_id = uuid.uuid4()
    build_data = generative_design_execution_dict.copy()
    build_data["id"] = str(generative_design_execution_id)

    # When
    execution: GenerativeDesignExecution = collection.build(build_data)

    # Then
    assert execution.uid == generative_design_execution_id
    assert execution.project_id == collection.project_id
    assert execution._session == collection.session
    assert execution.in_progress() and not execution.succeeded() and not execution.failed()

# TODO: Double check the path.
def test_trigger_execution(collection: GenerativeDesignExecutionCollection, generative_design_execution_dict, session):
    # Given
    session.set_response(generative_design_execution_dict)
    design_execuption_input = GenerativeDesignExecutionInput(
        seeds = ["CC(O)=O"],
        fingerprint_type = "ECFP4",
        min_fingerprint_similarity = 0.5,
        mutation_per_seed = 2
    )

    # When
    actual_execution = collection.trigger(design_execuption_input)

    # Then
    assert str(actual_execution.uid) == generative_design_execution_dict["id"]
    expected_path = '/projects/{}/generative-design/executions'.format(
        collection.project_id,
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json={
            'seeds': design_execuption_input.seeds,
            'fingerprint_type': design_execuption_input.fingerprint_type,
            'min_fingerprint_similarity': design_execuption_input.min_fingerprint_similarity,
            'mutation_per_seed': design_execuption_input.mutation_per_seed
        }
    )



