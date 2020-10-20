from time import time, sleep
from pprint import pprint
from citrine._rest.collection import Collection
from citrine.informatics.modules import Module
from citrine.resources.workflow_executions import (
    WorkflowExecution,
    WorkflowExecutionStatus,
)


class ConditionTimeoutError(RuntimeError):
    """Error that is raised when timeout is reached but the checked condition is still False."""

    pass


def _print_validation_status(
    status: str, start_time: float, line_start: str = "", line_end: str = "\r"
):
    print(
        "{}Status = {:<25}Elapsed time".format(line_start, status),
        " = {}s".format(str(int(time() - start_time)).rjust(3)),
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
        " = {}s".format(str(int(time() - start_time)).rjust(3)),
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
    start = time()

    def is_validated():
        status = collection.get(module.uid).status
        if print_status_info:
            _print_validation_status(status, start)
        return status != "VALIDATING" and status != "INPROGRESS"

    while not is_validated() and time() - start < timeout:
        sleep(interval)
    if not is_validated():
        msg = "Timeout reached, but condition is still {}".format(is_validated())
        raise ConditionTimeoutError(msg)

    if print_status_info:
        print("\nStatus info:")
        status_info = collection.get(module.uid).status_info
        pprint(status_info)

    return collection.get(module.uid)


def wait_while_executing(
    execution: WorkflowExecution,
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0,
) -> WorkflowExecution:
    """
    [ALPHA] Wait until execution is finished.

    Parameters
    ----------
    execution : WorkflowExecution
        WorklflowExecution to monitor
    print_status_info : bool, optional
        Whether to print status info, by default False
    timeout : float, optional
        Maximum time spent inquiring in seconds, by default 1800.0
    interval : float, optional
        Inquiry interval in seconds, by default 3.0

    Returns
    -------
    WorkflowExecution
        WorkflowExecution after execution


    Raises
    ------
    ConditionTimeoutError
        If fails to finish execution within timeout

    """
    start = time()

    def execution_is_finished():
        status = execution.status()
        if print_status_info:
            _print_execution_status(status, start)
        return not status.in_progress

    while not execution_is_finished() and (time() - start < timeout):
        sleep(interval)
    if not execution_is_finished():
        msg = "Timeout reached, but condition is still {}".format(execution_is_finished())
        raise ConditionTimeoutError(msg)
    return execution
