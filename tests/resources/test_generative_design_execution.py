import pytest
import uuid

from citrine.informatics.generative_design import GenerativeDesignInput
from citrine.informatics.executions.generative_design_execution import GenerativeDesignExecution
from citrine.resources.generative_design_execution import GenerativeDesignExecutionCollection
from citrine.informatics.generative_design import FingerprintType, StructureExclusion
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


def test_build_new_execution(collection, generative_design_execution_dict):
    execution: GenerativeDesignExecution = collection.build(generative_design_execution_dict)

    assert str(execution.uid) == generative_design_execution_dict["id"]
    assert execution.project_id == collection.project_id
    assert execution._session == collection.session
    assert execution.in_progress() and not execution.succeeded() and not execution.failed()
    assert execution.status_detail


def test_trigger_execution(collection: GenerativeDesignExecutionCollection, generative_design_execution_dict, session):
    # Given
    session.set_response(generative_design_execution_dict)
    design_execution_input = GenerativeDesignInput(
        seeds=["CC(O)=O"],
        fingerprint_type=FingerprintType.ECFP4,
        min_fingerprint_similarity=0.5,
        mutation_per_seed=2,
        structure_exclusions=[StructureExclusion.BROMINE, StructureExclusion.IODINE],
        min_substructure_counts={"C": 1, "O": 1},
    )

    # When
    actual_execution = collection.trigger(design_execution_input)

    # Then
    assert str(actual_execution.uid) == generative_design_execution_dict["id"]
    expected_path = '/projects/{}/generative-design/executions'.format(
        collection.project_id,
    )
    assert session.last_call == FakeCall(
        method='POST',
        path=expected_path,
        json={
            'seeds': design_execution_input.seeds,
            'fingerprint_type': design_execution_input.fingerprint_type.value,
            'min_fingerprint_similarity': design_execution_input.min_fingerprint_similarity,
            'mutation_per_seed': design_execution_input.mutation_per_seed,
            'structure_exclusions': [
                exclusion.value for exclusion in design_execution_input.structure_exclusions
            ],
            'min_substructure_counts': design_execution_input.min_substructure_counts,
        }
    )


def test_generative_design_execution_results(generative_design_execution: GenerativeDesignExecution, session, example_generation_results):
    # Given
    session.set_response(example_generation_results)

    # When
    list(generative_design_execution.results(per_page=4))

    # Then
    expected_path = '/projects/{}/generative-design/executions/{}/results'.format(
        generative_design_execution.project_id,
        generative_design_execution.uid,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path, params={"per_page": 4, "page": 1})


def test_generative_design_execution_result(generative_design_execution: GenerativeDesignExecution, session, example_generation_results):
    # Given
    session.set_response(example_generation_results["response"][0])

    # When
    result_id=example_generation_results["response"][0]["id"]
    generative_design_execution.result(result_id=result_id)

    # Then
    expected_path = '/projects/{}/generative-design/executions/{}/results/{}'.format(
        generative_design_execution.project_id,
        generative_design_execution.uid,
        result_id,
    )
    assert session.last_call == FakeCall(method='GET', path=expected_path)


def test_list(collection: GenerativeDesignExecutionCollection, session):
    session.set_response({"page": 1, "per_page": 4, "next": "", "response": []})
    lst = list(collection.list(per_page=4))
    assert len(lst) == 0

    expected_path = '/projects/{}/generative-design/executions'.format(collection.project_id)
    assert session.last_call == FakeCall(
        method='GET',
        path=expected_path,
        params={"page": 1, "per_page": 4}
    )


def test_delete(collection):
    with pytest.raises(NotImplementedError):
        collection.delete(uuid.uuid4())
