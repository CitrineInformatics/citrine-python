from copy import deepcopy
import uuid

import pytest

from citrine.resources.predictor_evaluation import PredictorEvaluationCollection
from citrine.informatics.executions.predictor_evaluation import PredictorEvaluationRequest
from citrine.informatics.predictors import GraphPredictor
from citrine.jobs.waiting import wait_while_executing

from tests.utils.factories import CrossValidationEvaluatorFactory, PredictorEvaluationDataFactory,\
    PredictorEvaluationFactory, PredictorInstanceDataFactory, PredictorRefFactory
from tests.utils.session import FakeCall, FakeSession


def paging_response(*items):
    return {"response": items}


def test_get():
    evaluation_response = PredictorEvaluationFactory()
    id = uuid.uuid4()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(evaluation_response)

    pec.get(id)

    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pec.project_id}/predictor-evaluations/{id}',
        params={}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_archived():
    evaluation_response = PredictorEvaluationFactory(is_archived=True)
    id = uuid.uuid4()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(evaluation_response)

    pec.archive(id)

    expected_call = FakeCall(
        method='PUT',
        path=f'/projects/{pec.project_id}/predictor-evaluations/{id}/archive',
        json={}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_restore():
    evaluation_response = PredictorEvaluationFactory()
    id = uuid.uuid4()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(evaluation_response)

    pec.restore(id)

    expected_call = FakeCall(
        method='PUT',
        path=f'/projects/{pec.project_id}/predictor-evaluations/{id}/restore',
        json={}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_list():
    evaluation_response = PredictorEvaluationFactory()
    pred_id = uuid.uuid4()
    pred_ver = 2

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(paging_response(evaluation_response))

    evaluations = list(pec.list(predictor_id=pred_id, predictor_version=pred_ver))

    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pec.project_id}/predictor-evaluations',
        params={"page": 1, "per_page": 100, "predictor_id": str(pred_id), "predictor_version": pred_ver, "archived": False}
    )

    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(evaluations) == 1


def test_list_archived():
    evaluation_response = PredictorEvaluationFactory(is_archived=True)
    pred_id = uuid.uuid4()
    pred_ver = 2

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(paging_response(evaluation_response))

    evaluations = list(pec.list_archived(predictor_id=pred_id, predictor_version=pred_ver))

    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pec.project_id}/predictor-evaluations',
        params={"page": 1, "per_page": 100, "predictor_id": str(pred_id), "predictor_version": pred_ver, "archived": True}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(evaluations) == 1


def test_list_all():
    evaluations = [PredictorEvaluationFactory(), PredictorEvaluationFactory(is_archived=True)]
    pred_id = uuid.uuid4()
    pred_ver = 2

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(paging_response(*evaluations))

    evaluations = list(pec.list_all(predictor_id=pred_id, predictor_version=pred_ver))

    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pec.project_id}/predictor-evaluations',
        params={"page": 1, "per_page": 100, "predictor_id": str(pred_id), "predictor_version": pred_ver, "archived": None}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(evaluations) == 2


def test_trigger():
    evaluators = [CrossValidationEvaluatorFactory()]
    pred_ref = PredictorRefFactory()
    evaluation_response = PredictorEvaluationFactory()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(evaluation_response)

    pec.trigger(predictor_id=pred_ref["predictor_id"], predictor_version=pred_ref["predictor_version"], evaluators=evaluators)

    expected_payload = PredictorEvaluationRequest(evaluators=evaluators,
                                                  predictor_id=pred_ref["predictor_id"],
                                                  predictor_version=pred_ref["predictor_version"])
    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{pec.project_id}/predictor-evaluations/trigger',
        json=expected_payload.dump()
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_trigger_default():
    evaluation_response = PredictorEvaluationFactory()
    pred_ref = PredictorRefFactory()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(evaluation_response)

    pec.trigger_default(predictor_id=pred_ref["predictor_id"], predictor_version=pred_ref["predictor_version"])

    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{pec.project_id}/predictor-evaluations/trigger-default',
        json=pred_ref
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_default():
    response = PredictorEvaluationDataFactory()
    pred_ref = PredictorRefFactory()

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(response)

    default_evaluators = pec.default(predictor_id=pred_ref["predictor_id"], predictor_version=pred_ref["predictor_version"])

    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{pec.project_id}/predictor-evaluations/default',
        json=pred_ref
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(default_evaluators) == len(response["evaluators"])

def test_default_from_config(valid_graph_predictor_data):
    response = PredictorEvaluationDataFactory()
    config = GraphPredictor.build(valid_graph_predictor_data)
    payload = config.dump()['instance']

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    session.set_response(response)

    default_evaluators = pec.default_from_config(config)

    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{pec.project_id}/predictor-evaluations/default-from-config',
        json=payload
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(default_evaluators) == len(response["evaluators"])


def test_register_not_implemented():
    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    with pytest.raises(NotImplementedError):
        pec.register(PredictorEvaluationDataFactory())


def test_update_not_implemented():
    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    with pytest.raises(NotImplementedError):
        pec.update(PredictorEvaluationDataFactory())


def test_delete_not_implemented():
    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    with pytest.raises(NotImplementedError):
        pec.delete(uuid.uuid4())


def test_wait():
    in_progress_response = PredictorEvaluationFactory(metadata__status={"major": "INPROGRESS", "minor": "EXECUTING", "detail": []})
    completed_response = deepcopy(in_progress_response)
    completed_response["metadata"]["status"]["major"] = "SUCCEEDED"
    completed_response["metadata"]["status"]["minor"] = "COMPLETED"

    session = FakeSession()
    pec = PredictorEvaluationCollection(uuid.uuid4(), session)
    
    # wait_while_executing makes two additional calls once it's done polling.
    responses = 4 * [in_progress_response] + 3 * [completed_response]
    session.set_responses(*responses)

    evaluation = pec.build(in_progress_response)
    wait_while_executing(collection=pec, execution=evaluation, interval=0.1)

    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pec.project_id}/predictor-evaluations/{in_progress_response["id"]}'
    )
    assert (len(responses) * [expected_call]) == session.calls
