from time import time, sleep
from citrine.informatics.modules import Module
from citrine.informatics.workflows import Workflow


def wait_until(condition, timeout=30, interval=0.5):
    """Poll at the specified interval until the provided condition is truthy or the timeout (in seconds) is reached."""
    start = time()

    result = condition()
    while not result and time() - start < timeout:
        sleep(interval)
        result = condition()

    return result


def wait_while_ready(*, module: Module, **kwargs) -> Module:
    """Mock mutations of a successful module validation."""
    module.status = 'READY'
    module.status_info = ['Something went very right.']
    return module


def wait_while_succeeded(*, module: Workflow, **kwargs) -> Workflow:
    """Mock mutations of a successful workflow validation."""
    module.status = 'SUCCEEDED'
    module.status_info = ['Something went very right.']
    return module


def wait_while_invalid(*, module: Module, **kwargs) -> Module:
    """Mock mutations of a failed module validation."""
    module.status = 'INVALID'
    module.status_info = ['Something went very wrong.']
    return module


def wait_while_failed(*, module: Workflow, **kwargs) -> Workflow:
    """Mock mutations of a failed workflow validation."""
    module.status = 'FAILED'
    module.status_info = ['Something went very wrong.']
    return module
