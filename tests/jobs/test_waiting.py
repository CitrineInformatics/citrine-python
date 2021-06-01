"""Tests waiting utilities"""
import pytest
import mock
import io
import sys
from datetime import datetime
import time

from citrine.jobs.waiting import wait_while_executing, wait_while_validating, ConditionTimeoutError
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.design_execution import DesignExecution


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
    statuses = mock.PropertyMock(return_value="VALIDATING")
    type(module).status = statuses
    module.in_progress.return_value = True
    collection.get.return_value = module

    with pytest.raises(ConditionTimeoutError):
        wait_while_validating(collection, module, timeout=1.0)


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

    wait_while_executing(collection, workflow_execution, print_status_info=True)

    assert("SUCCEEDED" in captured_output.getvalue())
