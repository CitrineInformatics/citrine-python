import pytest
import re

from citrine.resources.response import Response


def test_response_repr():

    resp = Response()
    no_body_found = re.search("No body available", resp.__repr__())
    no_status_code_found = re.search("No HTTP status available", resp.__repr__())
    assert no_body_found
    assert no_status_code_found

    resp_with_code = Response(status_code=404)
    no_body_found = re.search("No body available", resp_with_code.__repr__())
    status_code_found = re.search("404", resp_with_code.__repr__())
    assert no_body_found
    assert status_code_found

    resp_with_code_and_body = Response(status_code=404, body={"message": "a quick message"})
    body_found = re.search("a quick message", resp_with_code_and_body.__repr__())
    status_code_found = re.search("404", resp_with_code_and_body.__repr__())
    assert body_found
    assert status_code_found
