import time
from pprint import pprint
from citrine._rest.collection import Collection
from citrine._rest.asynchronous_object import AsynchronousObject
from citrine.informatics.modules import Module
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.design_execution import DesignExecution
from citrine.resources.workflow_executions import (
    WorkflowExecution,
    WorkflowExecutionStatus,
)
from typing import Union, Optional


class ConditionTimeoutError(RuntimeError):
    """Error that is raised when timeout is reached but the checked condition is still False."""

    pass


def _print_string_status(
    status: str, start_time: float, line_start: str = "", line_end: str = "\r"
):
    print(
        "{}Status = {:<25}Elapsed time".format(line_start, status),
        " = {}s".format(str(int(time.time() - start_time)).rjust(3)),
        end=line_end,
    )


def _pretty_execution_status(status: WorkflowExecutionStatus):
    status_text = status.status
    output_text = status_text if status_text != "InProgress" else "In progress"
    return output_text


def _print_execution_status(
    status: WorkflowExecutionStatus, start_time: float, line_end: str = "\r"
):
    print(
        "Status = {:<25}Elapsed time".format(_pretty_execution_status(status)),
        " = {}s".format(str(int(time.time() - start_time)).rjust(3)),
        end=line_end,
    )


def wait_for_asynchronous_object(
    resource: Union[AsynchronousObject, WorkflowExecution],
    collection: Optional[Collection[AsynchronousObject]] = None,
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0
) -> Union[AsynchronousObject, WorkflowExecution]:
    """
    Wait until an asynchronous object has finished.

    This could be a module, workflow, workflow execution, or report.
    WorkflowExecution is deprecated, and once it is removed the special logic required here
    for WorkflowExecutions can be removed.

    Parameters
    ----------
    resource: Union[AsynchronousObject, WorkflowExecution]
        a module, workflow, workflow execution, or report to monitor
    collection: Optional[Collection[AsynchronousObjet]]
        Collection containing the resource. Not necessary for WorkflowExecution
    print_status_info: bool
        Whether to print status info, by default False
    timeout : float
        Maximum time spent waiting, in seconds, by default 1800.0
    interval: float
        Inquiry interval in seconds, by default 3.0

    Returns
    -------
    Union[AsynchronousObject, WorkflowExecution]
        The resource after the asynchronous work has finished or timed out.

    Raises
    ------
    ConditionTimeoutError
        If fails to finish within timeout

    """
    start = time.time()

    def is_finished():
        if isinstance(resource, WorkflowExecution):
            status = resource.status()
            if print_status_info:
                _print_execution_status(status, start)
            return not status.in_progress
        else:
            if collection is None:
                raise ValueError("Must provide collection")
            current_resource = collection.get(resource.uid)
            if print_status_info:
                _print_string_status(current_resource.status, start)
            in_progress = current_resource.in_progress()
            return not in_progress

    while not is_finished() and (time.time() - start < timeout):
        time.sleep(interval)
    if not is_finished():
        raise ConditionTimeoutError("Timeout reached, but task is still in progress")

    if isinstance(resource, WorkflowExecution):
        return resource
    else:
        current_resource = collection.get(resource.uid)
        if print_status_info and hasattr(current_resource, 'status_info'):
            print("\nStatus info:")
            pprint(current_resource.status_info)
        return current_resource


def wait_while_validating(
    collection: Collection[Module],
    module: Module,
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0,
) -> Module:
    """
    Wait until module is validated.

    Parameters
    ----------
    collection : Collection[Module]
        Collection containing module
    module : Module
        Module in Collection
    print_status_info : bool, optional
        Whether to print status info, by default False
    timeout : float, optional
        Maximum time spent inquiring in seconds, by default 1800.0
    interval : float, optional
        Inquiry interval in seconds, by default 3.0

    Returns
    -------
    Module
        Module in Collection after validation

    Raises
    ------
    ConditionTimeoutError
        If fails to validate within timeout

    """
    return wait_for_asynchronous_object(module, collection, print_status_info, timeout, interval)


def wait_while_executing(
    execution: Union[WorkflowExecution, PredictorEvaluationExecution, DesignExecution],
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0,
    collection: Collection[Module] = None,
) -> Union[WorkflowExecution, PredictorEvaluationExecution, DesignExecution]:
    """
    Wait until execution is finished.

    Parameters
    ----------
    execution : WorkflowExecution, PredictorEvaluationExecution or DesignExecution
        an execution to monitor
    print_status_info : bool, optional
        Whether to print status info, by default False
    timeout : float, optional
        Maximum time spent inquiring in seconds, by default 1800.0
    interval : float, optional
        Inquiry interval in seconds, by default 3.0
    collection : Collection[Module]
        Collection containing module, not needed for deprecated WorkflowExecution

    Returns
    -------
    WorkflowExecution, PredictorEvaluationExecution or DesignExecution
        the updated execution after it has finished executing


    Raises
    ------
    ConditionTimeoutError
        If fails to finish execution within timeout

    """
    return wait_for_asynchronous_object(execution, collection,
                                        print_status_info, timeout, interval)
