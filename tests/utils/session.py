from json import dumps
from urllib.parse import urlencode


class FakeCall:
    """
    Encapsulates a call to a FakeSession
    """

    def __init__(self, method, path, json=None, params: dict = None):
        self.method = method
        self.path = path
        self.json = json
        self.params = params or {}

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
    """
    Fake version of Session used to test API interaction
    """
    def __init__(self):
        self.calls = []
        self.response = {}

    def set_response(self, resp):
        self.response = resp

    @property
    def num_calls(self) -> int:
        return len(self.calls)

    @property
    def last_call(self) -> FakeCall:
        return self.calls[-1]

    def get_resource(self, path: str, *args, **kwargs) -> dict:
        self.calls.append(FakeCall('GET', path, params=kwargs.get('params')))
        return self.response

    def post_resource(self, path: str, json: dict, *args, **kwargs) -> dict:
        self.calls.append(FakeCall('POST', path, json))
        return self.response

    def put_resource(self, path: str, json: dict, *args, **kwargs) -> dict:
        self.calls.append(FakeCall('PUT', path, json))
        return self.response

    def delete_resource(self, path: str) -> dict:
        self.calls.append(FakeCall('DELETE', path))
        return self.response

