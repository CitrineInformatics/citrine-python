from json import dumps
from typing import Callable, Iterator, List
from urllib.parse import urlencode

from citrine.exceptions import NonRetryableHttpException
from citrine.resources.api_error import ValidationError


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
    def __init__(self, *, accounts_v3=False):
        self.calls = []
        self.responses = []
        self.s3_endpoint_url = None
        self.s3_use_ssl = True
        self.s3_addressing_style = 'auto'
        self.use_idempotent_dataset_put = False
        self._accounts_service_v3 = accounts_v3

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

    def patch_resource(self, path: str, json: dict, **kwargs) -> dict:
        return self.checked_patch(path, json, **kwargs)

    def delete_resource(self, path: str, **kwargs) -> dict:
        return self.checked_delete(path, **kwargs)

    def checked_get(self, path: str, **kwargs) -> dict:
        self.calls.append(FakeCall('GET', path, params=kwargs.get('params')))
        return self._get_response()

    def checked_post(self, path: str, json: dict, **kwargs) -> dict:
        self.calls.append(FakeCall('POST', path, json, params=kwargs.get('params')))
        return self._get_response(default_response=json)

    def checked_put(self, path: str, json: dict, **kwargs) -> dict:
        self.calls.append(FakeCall('PUT', path, json, params=kwargs.get('params')))
        return self._get_response(default_response=json)

    def checked_patch(self, path: str, json: dict, **kwargs) -> dict:
        self.calls.append(FakeCall('PATCH', path, json, params=kwargs.get('params')))
        return self._get_response(default_response=json)

    def checked_delete(self, path: str, **kwargs) -> dict:
        if 'json' in kwargs:
            self.calls.append(FakeCall('DELETE', path, kwargs.get('json'), params=kwargs.get('params')))
        else:
            self.calls.append(FakeCall('DELETE', path, params=kwargs.get('params')))
        return self._get_response()

    def _get_response(self, default_response: dict = None):
        """
        Returns responses in order, repeating the final response indefinitely.
        """
        if not self.responses:
            if not default_response:
                default_response = {}
            return default_response

        response = self.responses.pop(0)
        if isinstance(response, NonRetryableHttpException):
            raise response
        return response

    @staticmethod
    def cursor_paged_resource(base_method: Callable[..., dict], path: str,
                              forward: bool = True, per_page: int = 100,
                              version: str = 'v2', **kwargs) -> Iterator[dict]:
        """
        Returns a flat generator of results for an API query.

        Results are fetched in chunks of size `per_page` and loaded lazily.
        """
        params = kwargs.get('params', {})
        params['forward'] = forward
        params['ascending'] = forward
        params['per_page'] = per_page
        kwargs['params'] = params
        while True:
            response_json = base_method(path, version=version, **kwargs)
            for obj in response_json['contents']:
                yield obj
            cursor = response_json.get('next')
            if cursor is None:
                break
            params['cursor'] = cursor


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

        # in case the response takes the shape of something like 
        # {'projects': [Project1, Project2, etc.]}
        has_collection_key = isinstance(self.responses[0], dict)

        if has_collection_key:
            key = list(self.responses[0].keys())[0]
            list_values = self.responses[0][key][start_idx:start_idx + per_page]
            return dict.fromkeys([key], list_values)

        else:
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

    def __init__(self, status_code, content=None, text="", reason='BadRequest'):
        self.content = content
        self.text = text
        self.status_code = status_code
        self.reason = reason
        self.request = FakeRequest()

    def json(self):
        return self.content


# TODO: Generalize. That is, don't require validation_errors, don't assume "BadRequest", and pass
#       the method to FakeRequest.
class FakeRequestResponseApiError:
    """A fake version of a requests.request() response that has an ApiError"""
    def __init__(self, code: int, message: str, validation_errors: List[ValidationError],
                 reason: str = 'BadRequest'):
        self.api_error_json = {"code": code,
                               "message": message,
                               "validation_errors": [ve.as_dict() for ve in validation_errors]}
        self.text = message
        self.status_code = code
        self.reason = reason
        self.request = FakeRequest()

    def json(self):
        return self.api_error_json


class FakeRequest:
    # Defaults to PATCH for legacy reasons.
    # TODO: require the method to be passed.
    def __init__(self):
        self.method = "PATCH"


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
