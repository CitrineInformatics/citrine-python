from time import time, sleep
from typing import List, Optional, Callable

from citrine.resources.status_detail import StatusDetail


def wait_until(condition, timeout=30, interval=0.5):
    """Poll at the specified interval until the provided condition is truthy or the timeout (in seconds) is reached."""
    start = time()

    result = condition()
    while not result and time() - start < timeout:
        sleep(interval)
        result = condition()

    return result


def generate_fake_wait_while(*, status: str, status_detail: Optional[List[StatusDetail]] = None) -> Callable:
    """Generate a wait_while function that mutates a resource with the specified status info."""
    status_detail = status_detail or []

    def _wait_while_status(**kwargs):
        # We need either a `module` or `execution` argument
        if "module" in kwargs:
            module = kwargs["module"]
            module.status = status
            module.status_detail = status_detail
            return module
        elif "execution" in kwargs:
            execution = kwargs["execution"]
            execution.status = status
            execution.status_detail = StatusDetail(msg=status, level="Unknown")
            return execution

    return _wait_while_status
