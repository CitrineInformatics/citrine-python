from json import dumps
from urllib.parse import urlencode


class FakeCall:
    """Encapsulates a call to a FakeSession."""

    def __init__(self, method, path, json=None, params: dict = None):
        self.method = method
        self.path = path
        self.json = json
        self.params = params or {}

    def __repr__(self):
        return 'FakeCall({})'.format(self)

    def __str__(self) -> str:
        path = self.path
        if self.params:
            path = '{}?{}'.format(self.path, urlencode(self.params))

        return '{} {} : {}'.format(self.method, path, dumps(self.json))

    def __eq__(self, other) -> bool:
        if not isinstance(other, FakeCall):
            return NotImplemented

        return self.method == other.method and \
            self.path == other.path and \
            self.json == other.json and \
            self.params == other.params


class FakeSession:
    """Fake version of Session used to test API interaction."""
    def __init__(self):
        self.calls = []
        self.responses = []
        self.s3_endpoint_url = None
        self.s3_use_ssl = True
        self.s3_addressing_style = 'auto'

    def set_response(self, resp):
        self.responses = [resp]

    def set_responses(self, *resps):
        self.responses = list(resps)

    @property
    def num_calls(self) -> int:
        return len(self.calls)

    @property
    def last_call(self) -> FakeCall:
        return self.calls[-1]

    def get_resource(self, path: str, **kwargs) -> dict:
        return self.checked_get(path, **kwargs)

    def post_resource(self, path: str, json: dict, **kwargs) -> dict:
        return self.checked_post(path, json, **kwargs)

    def put_resource(self, path: str, json: dict, **kwargs) -> dict:
        return self.checked_put(path, json, **kwargs)

    def delete_resource(self, path: str) -> dict:
        return self.checked_delete(path)

    def checked_get(self, path: str, **kwargs) -> dict:
        self.calls.append(FakeCall('GET', path, params=kwargs.get('params')))
        return self._get_response()

    def checked_post(self, path: str, json: dict, **kwargs) -> dict:
        self.calls.append(FakeCall('POST', path, json, params=kwargs.get('params')))
        return self._get_response()

    def checked_put(self, path: str, json: dict, **kwargs) -> dict:
        self.calls.append(FakeCall('PUT', path, json))
        return self._get_response()

    def checked_delete(self, path: str) -> dict:
        self.calls.append(FakeCall('DELETE', path))
        return self._get_response()

    def _get_response(self):
        """
        Returns responses in order, repeating the final response indefinitely.
        """
        if not self.responses:
            return {}

        if len(self.responses) > 1:
            return self.responses.pop(0)

        return self.responses[0]


class FakePaginatedSession(FakeSession):
    """Fake version of Session used to test API interaction, with support for pagination params page and per_page."""
    def checked_get(self, path: str, **kwargs) -> dict:
        params = kwargs.get('params')
        self.calls.append(FakeCall('GET', path, params=params))
        return self._get_response(**params)

    def checked_post(self, path: str, json: dict, **kwargs) -> dict:
        params = kwargs.get('params')
        self.calls.append(FakeCall('POST', path, json, params=params))
        return self._get_response(**params)

    def _get_response(self, **kwargs):
        """
        Returns responses using the page and per_page parameters (if supplied).  This emulates a paginated API response.
        """
        if not self.responses:
            return {}

        page = kwargs.get('page', 1)
        per_page = kwargs.get('per_page', 20)

        start_idx = (page - 1) * per_page
        return self.responses[0][start_idx:start_idx + per_page]


class FakeS3Client:
    """A fake version of the S3 client that has a put_object method."""

    def __init__(self, put_object_output):
        self.put_object_output = put_object_output

    def put_object(self, *args, **kwargs):
        """Return the expected output of the real client's put_object method."""
        return self.put_object_output


class FakeRequestResponse:
    """A fake version of a requests.request() response."""

    def __init__(self, content=None):
        self.content = content


def make_fake_cursor_request_function(all_results: list):
    """
    Returns function which simulates request to cursor-paged endpoint.

    Parameters
    ---------
    all_results: list
        All results in the result set to simulate paging
    """
    # TODO add logic for `forward` and `ascending`
    def fake_cursor_request(*_, params=None, **__):
        page_size = params['per_page']
        if 'cursor' in params:
            cursor = int(params['cursor'])
            contents = all_results[cursor + 1:cursor + page_size + 1]
        else:
            contents = all_results[:page_size]
        response = {'contents': contents}
        if contents:
            response['next'] = str(all_results.index(contents[-1]))
            if 'cursor' in params:
                response['previous'] = str(all_results.index(contents[0]))
        return response
    return fake_cursor_request
