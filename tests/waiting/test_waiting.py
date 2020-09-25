"""Tests waiting utilities"""
import pytest
import mock
import io
import sys

from citrine.waiting.waiting import wait_while_executing, wait_while_validating, ConditionTimeoutError

def test_wait_while_validating():

    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    module = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["VALIDATING", "VALID", "VALID"])
    type(module).status = statuses
    collection.get.return_value = module

    wait_while_validating(collection, module)

    assert("VALID" in captured_output.getvalue())

def test_wait_while_validating_timeout():
    captured_output = io.StringIO()
    sys.stdout = captured_output

    collection = mock.Mock()
    module = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["VALIDATING"] * 1000)
    type(module).status = statuses
    collection.get.return_value = module

    with pytest.raises(ConditionTimeoutError):
        wait_while_validating(collection, module, timeout=1.0)

def test_wait_while_executing():

    captured_output = io.StringIO()
    sys.stdout = captured_output

    workflow_execution = mock.Mock()
    execution_status = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["InProgress", "Finished", "Finished"])
    in_progress = mock.PropertyMock(side_effect = [True, False, False])
    type(execution_status).status = statuses
    type(execution_status).in_progress = in_progress
    workflow_execution.status.return_value = execution_status

    wait_while_executing(workflow_execution)

    assert("Finished" in captured_output.getvalue())


def test_while_executing_timeout():
    
    captured_output = io.StringIO()
    sys.stdout = captured_output

    workflow_execution = mock.Mock()
    execution_status = mock.Mock()
    statuses = mock.PropertyMock(side_effect = ["InProgress"]*1000)
    in_progress = mock.PropertyMock(side_effect = [True]*1000)
    type(execution_status).status = statuses
    type(execution_status).in_progress = in_progress
    workflow_execution.status.return_value = execution_status

    with pytest.raises(ConditionTimeoutError):
        wait_while_executing(workflow_execution, timeout=1.0)