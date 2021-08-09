"""Tests waiting utilities"""
from datetime import datetime
import io
import mock
import pytest
import sys
import time

from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.executions.predictor_evaluation_execution import PredictorEvaluationExecution
from src.citrine.jobs.waiting import wait_for_asynchronous_object, wait_while_executing, wait_while_validating, ConditionTimeoutError


@mock.patch('time.sleep', return_value=None)
def test_wait_while_validating(sleep_mock):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    module = mock.Mock()
    statuses = mock.PropertyMock(side_effect=["VALIDATING", "VALID", "VALID"])
    status_info = mock.PropertyMock(return_value="The predictor is now validated.")
    in_progress = mock.PropertyMock(side_effect=[True, False, False])
    type(module).status = statuses
    type(module).status_info = status_info
    module.in_progress = in_progress
    collection.get.return_value = module

    wait_while_validating(collection=collection, module=module, print_status_info=True)

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
    statuses = mock.PropertyMock(return_value="VALIDATING")
    type(module).status = statuses
    module.in_progress.return_value = True
    collection.get.return_value = module

    with pytest.raises(ConditionTimeoutError) as exceptio:
        wait_while_validating(collection=collection, module=module, timeout=1.0)


@mock.patch('time.sleep', return_value=None)
def test_wait_while_executing(sleep_mock):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    workflow_execution = mock.Mock(spec=DesignExecution)
    statuses = mock.PropertyMock(side_effect=["INPROGRESS", "SUCCEEDED", "SUCCEEDED"])
    in_progress = mock.PropertyMock(side_effect=[True, False, False])
    type(workflow_execution).status = statuses
    workflow_execution.in_progress = in_progress
    collection.get.return_value = workflow_execution

    wait_while_executing(collection=collection, execution=workflow_execution, print_status_info=True)

    assert("SUCCEEDED" in captured_output.getvalue())

@mock.patch('time.time')
@mock.patch('time.sleep', return_value=None)
def test_wait_for_asynchronous_object(sleep_mock, time_mock):
    time_mock.side_effect = [
        time.mktime(datetime(2021, 8, 1).timetuple()),
        time.mktime(datetime(2021, 8, 2).timetuple())
    ]

    resource = mock.Mock()
    collection = mock.Mock()
    type(resource).uid = mock.PropertyMock(return_value=123456)

    with pytest.raises(ConditionTimeoutError) as exception:
        wait_for_asynchronous_object(collection=collection, resource=resource, timeout=1.0)

    assert "123456" in str(exception.value)
