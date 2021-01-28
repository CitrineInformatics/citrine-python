import time
from pprint import pprint
from citrine._rest.collection import Collection
from citrine.informatics.modules import Module
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.design_execution import DesignExecution
from citrine.resources.workflow_executions import (
    WorkflowExecution,
    WorkflowExecutionStatus,
)
from typing import Union


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
    start = time.time()

    def is_validated():
        status = collection.get(module.uid).status
        if print_status_info:
            _print_string_status(status, start)
        return status != "VALIDATING" and status != "INPROGRESS"

    while not is_validated() and time.time() - start < timeout:
        time.sleep(interval)
    if not is_validated():
        msg = "Timeout reached, but condition is still {}".format(is_validated())
        raise ConditionTimeoutError(msg)

    if print_status_info:
        print("\nStatus info:")
        status_info = collection.get(module.uid).status_info
        pprint(status_info)

    return collection.get(module.uid)


def wait_while_executing(
    execution: Union[WorkflowExecution, PredictorEvaluationExecution, DesignExecution],
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0,
    collection: Collection[Module] = None,
) -> Union[WorkflowExecution, PredictorEvaluationExecution, DesignExecution]:
    """
    [ALPHA] Wait until execution is finished.

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
        Collection containing module, only needed for PredictorEvaluationExecutions

    Returns
    -------
    WorkflowExecution, PredictorEvaluationExecution or DesignExecution
        the updated execution after it has finished executing


    Raises
    ------
    ConditionTimeoutError
        If fails to finish execution within timeout

    """
    start = time.time()

    def execution_is_finished():
        if isinstance(execution, (PredictorEvaluationExecution, DesignExecution)):
            if collection is None:
                raise ValueError("Must provide collection")
            status = collection.get(execution.uid).status
            if print_status_info:
                _print_string_status(status, start)
            return status != "INPROGRESS"
        else:
            status = execution.status()
            if print_status_info:
                _print_execution_status(status, start)
            return not status.in_progress

    while not execution_is_finished() and (time.time() - start < timeout):
        time.sleep(interval)
    if not execution_is_finished():
        msg = "Timeout reached, but condition is still {}".format(execution_is_finished())
        raise ConditionTimeoutError(msg)

    # re-fetch the execution if we have a collection to fetch it with
    if collection is not None:
        execution = collection.get(execution.uid)
    return execution
