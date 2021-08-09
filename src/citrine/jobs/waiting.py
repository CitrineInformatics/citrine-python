import time
from pprint import pprint
from typing import Union

from citrine._rest.collection import Collection
from citrine._rest.asynchronous_object import AsynchronousObject
from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.executions import PredictorEvaluationExecution
from citrine.informatics.modules import Module


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


def wait_for_asynchronous_object(
    *,
    resource: AsynchronousObject,
    collection: Collection[AsynchronousObject],
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0
) -> AsynchronousObject:
    """
    Wait until an asynchronous object has finished.

    This could be a module, workflow, workflow execution, or report.

    Parameters
    ----------
    resource: AsynchronousObject
        a module, workflow, workflow execution, or report to monitor
    collection: Collection[AsynchronousObject]
        Collection containing the resource
    print_status_info: bool
        Whether to print status info, by default False
    timeout : float
        Maximum time spent waiting, in seconds, by default 1800.0
    interval: float
        Inquiry interval in seconds, by default 3.0

    Returns
    -------
    AsynchronousObject
        The resource after the asynchronous work has finished or timed out.

    Raises
    ------
    ConditionTimeoutError
        If fails to finish within timeout

    """
    start = time.time()

    def is_finished():
        current_resource = collection.get(resource.uid)
        if print_status_info:
            _print_string_status(current_resource.status, start)
        return not current_resource.in_progress()

    while not is_finished() and (time.time() - start < timeout):
        time.sleep(interval)
    if not is_finished():
        raise ConditionTimeoutError(
            "Timeout of {timeout_length} seconds "
            "reached, but task {uid} is still in progress".format(
                timeout_length=timeout, uid=resource.uid)
        )

    current_resource = collection.get(resource.uid)
    if print_status_info and hasattr(current_resource, 'status_info'):
        print("\nStatus info:")
        pprint(current_resource.status_info)
    return current_resource


def wait_while_validating(
    *,
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
    return wait_for_asynchronous_object(resource=module, collection=collection,
                                        print_status_info=print_status_info, timeout=timeout,
                                        interval=interval)


def wait_while_executing(
    *,
    collection: Union[Collection[PredictorEvaluationExecution], Collection[DesignExecution]],
    execution: Union[PredictorEvaluationExecution, DesignExecution],
    print_status_info: bool = False,
    timeout: float = 1800.0,
    interval: float = 3.0,
) -> Union[PredictorEvaluationExecution, DesignExecution]:
    """
    Wait until execution is finished.

    Parameters
    ----------
    execution : Union[PredictorEvaluationExecution, DesignExecution]
        an execution to monitor
    print_status_info : bool, optional
        Whether to print status info, by default False
    timeout : float, optional
        Maximum time spent inquiring in seconds, by default 1800.0
    interval : float, optional
        Inquiry interval in seconds, by default 3.0
    collection : Union[Collection[PredictorEvaluationExecution], Collection[DesignExecution]]
        Collection containing executions

    Returns
    -------
    Union[PredictorEvaluationExecution, DesignExecution]
        the updated execution after it has finished executing


    Raises
    ------
    ConditionTimeoutError
        If fails to finish execution within timeout

    """
    return wait_for_asynchronous_object(resource=execution, collection=collection,
                                        print_status_info=print_status_info, timeout=timeout,
                                        interval=interval)
