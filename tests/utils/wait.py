from time import time, sleep

def wait_until(condition, timeout=30, interval=0.5):
    """Poll at the specified interval until the provided condition is truthy or the timeout (in seconds) is reached."""
    start = time()

    result = condition()
    while not result and time() - start < timeout:
        sleep(interval)
        result = condition()

    return result