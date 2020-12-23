"""Tests waiting utilities"""
import pytest
import mock
import io
import sys
from datetime import datetime
import time

from citrine.jobs.waiting import wait_while_executing, wait_while_validating, ConditionTimeoutError
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution


@mock.patch('time.sleep', return_value=None)
def test_wait_while_validating(sleep_mock):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    module = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["VALIDATING", "VALID", "VALID"])
    status_info = mock.PropertyMock(return_value = "The predictor is now validated.")
    type(module).status = statuses
    type(module).status_info = status_info
    collection.get.return_value = module

    wait_while_validating(collection, module, print_status_info=True)

    assert("Status = VALID" in captured_output.getvalue())
    assert("The predictor is now validated." in captured_output.getvalue())


@mock.patch('time.time')
@mock.patch('time.sleep', return_value=None)
def test_wait_while_validating_timeout(sleep_mock, time_mock):
    time_mock.side_effect = [
        time.mktime(datetime(2020, 10, 30).timetuple()),
        time.mktime(datetime(2020, 10, 31).timetuple())
    ]

    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    module = mock.Mock()
    statuses = mock.PropertyMock(return_value = "VALIDATING")
    type(module).status = statuses
    collection.get.return_value = module

    with pytest.raises(ConditionTimeoutError):
        wait_while_validating(collection, module, timeout=1.0)


@mock.patch('time.sleep', return_value=None)
def test_wait_while_executing(sleep_mock):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    workflow_execution = mock.Mock()
    execution_status = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["InProgress", "Finished", "Finished"])
    in_progress = mock.PropertyMock(side_effect = [True, False, False])
    type(execution_status).status = statuses
    type(execution_status).in_progress = in_progress
    workflow_execution.status.return_value = execution_status

    wait_while_executing(workflow_execution, print_status_info=True)

    assert("Finished" in captured_output.getvalue())


@mock.patch('time.sleep', return_value=None)
def test_wait_while_executing_predictor_evaluation_execution(sleep_mock):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    predictor_evaluation_execution = mock.Mock(spec=PredictorEvaluationExecution)
    execution_status = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["INPROGRESS", "READY", "READY"])
    status_info = mock.PropertyMock(return_value = "???")
    type(predictor_evaluation_execution).status = statuses
    type(predictor_evaluation_execution).status_info = status_info
    collection.get.return_value = predictor_evaluation_execution

    wait_while_executing(predictor_evaluation_execution, print_status_info=True, collection=collection)
    assert("READY" in captured_output.getvalue())


def test_wait_while_executing_predictor_evaluation_execution_missing_collection():
    predictor_evaluation_execution = mock.Mock(spec=PredictorEvaluationExecution)

    with pytest.raises(ValueError):
        wait_while_executing(predictor_evaluation_execution, print_status_info=True)


@mock.patch('time.time')
@mock.patch('time.sleep', return_value=None)
def test_while_executing_timeout(sleep_mock, time_mock):
    time_mock.side_effect = [
        time.mktime(datetime(2020, 10, 30).timetuple()),
        time.mktime(datetime(2020, 10, 31).timetuple())
    ]
    
    captured_output = io.StringIO()
    sys.stdout = captured_output

    workflow_execution = mock.Mock()
    execution_status = mock.Mock()
    statuses = mock.PropertyMock(return_value = "InProgress")
    in_progress = mock.PropertyMock(return_value = True)
    type(execution_status).status = statuses
    type(execution_status).in_progress = in_progress
    workflow_execution.status.return_value = execution_status

    with pytest.raises(ConditionTimeoutError):
        wait_while_executing(workflow_execution, timeout=1.0)
