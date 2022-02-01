import platform
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from logging import getLogger
from os import environ
from typing import Optional, Callable, Iterator
from urllib.parse import urlunsplit
from warnings import warn

import jwt
import requests
import requests.auth
from requests import Response
from urllib3.util.retry import Retry

import citrine
from citrine._utils.functions import format_escaped_url
from citrine.exceptions import (
    BadRequest,
    CitrineException,
    Conflict,
    NotFound,
    Unauthorized,
    UnauthorizedRefreshToken,
    WorkflowNotReadyException)

# Choose a 5 second buffer so that there's no chance of the access token
# expiring during the check for expiration
EXPIRATION_BUFFER_MILLIS: timedelta = timedelta(milliseconds=5000)
logger = getLogger(__name__)


class Session(requests.Session):
    """Wrapper around requests.Session that is both refresh-token and schema aware."""

    def __init__(self,
                 refresh_token: str = None,
                 legacy_scheme: Optional[str] = None,
                 host: str = None,
                 port: Optional[str] = None,
                 *,
                 scheme: str = None):
        super().__init__()
        if refresh_token is None:
            refresh_token = environ.get('CITRINE_API_KEY')
        if legacy_scheme is not None:
            warn("Creating a session with positional arguments other than refresh_token "
                 "is deprecated; use keyword arguments to specify scheme, host and port.",
                 DeprecationWarning)
            if scheme is None:
                scheme = legacy_scheme
            else:
                raise ValueError("Specify legacy_scheme or scheme, not both.")
        elif scheme is None:
            scheme = 'https'
        if host is None:
            host = environ.get('CITRINE_API_HOST')
            if host is None:
                raise ValueError("No host passed and environmental "
                                 "variable CITRINE_API_HOST not set.")

        self.scheme: str = scheme
        self.authority = ':'.join(([host] if host else []) + ([port] if port else []))
        self.refresh_token: str = refresh_token
        self.access_token: Optional[str] = None
        self.access_token_expiration: datetime = datetime.utcnow()
        self._accounts_service_v3: bool = False

        agent = "{}/{} python-requests/{} citrine-python/{}".format(
            platform.python_implementation(),
            platform.python_version(),
            requests.__version__,
            citrine.__version__)

        # Following scheme:[//authority]path[?query][#fragment] (https://en.wikipedia.org/wiki/URL)
        self.headers.update({
            "Content-Type": "application/json",
            "User-Agent": agent})

        # Default parameters for S3 connectivity. Can be changed by tests.
        self.s3_endpoint_url = None
        self.s3_use_ssl = True
        self.s3_addressing_style = 'auto'

        # Feature flag for enabling the use of Dataset idempotent PUT. Will be removed
        # in a future release.
        self.use_idempotent_dataset_put = False

        # Custom adapter so we can use custom retry parameters. The default HTTP status
        # codes for retries are [503, 413, 429]. We're using status_force list to add
        # additional codes to retry on, focusing on specific CloudFlare 5XX errors.
        retries = Retry(total=10,
                        connect=5,
                        read=5,
                        status=5,
                        backoff_factor=0.25,
                        status_forcelist=[500, 502, 504, 520, 521, 522, 524, 527])
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.mount('https://', adapter)
        self.mount('http://', adapter)

        # Requests has it's own set of exceptions that do not inherit from the
        # built-in exceptions. The built-in ConnectionError handles 4 different
        # child exceptions: https://docs.python.org/3/library/exceptions.html#ConnectionError
        self.retry_errs = (ConnectionError,
                           requests.exceptions.ConnectionError,
                           requests.exceptions.ChunkedEncodingError)
        self._refresh_access_token()
        self._check_accounts_version()

    def _versioned_base_url(self, version: str = 'v1'):
        return urlunsplit((
            self.scheme,
            self.authority,
            format_escaped_url('api/{}/', version),
            '',  # query string
            ''  # fragment
        ))

    def _is_access_token_expired(self):
        return self.access_token_expiration - EXPIRATION_BUFFER_MILLIS <= datetime.utcnow()

    def _refresh_access_token(self) -> None:
        """Optionally refresh our access token (if the previous one is about to expire)."""
        data = {'refresh_token': self.refresh_token}

        response = self._request_with_retry('POST', self._versioned_base_url() + 'tokens/refresh',
                                            json=data)

        if response.status_code != 200:
            raise UnauthorizedRefreshToken()
        self.access_token = response.json()['access_token']
        self.access_token_expiration = datetime.utcfromtimestamp(
            jwt.decode(self.access_token, verify=False)['exp']
        )

        # Explicitly set an updated 'auth', so as to not rely on implicit cookie handling.
        self.auth = BearerAuth(self.access_token)

    def _check_accounts_version(self) -> None:
        """Checks Product to find out what version of Accounts is used."""
        response = self._request_with_retry('GET',
                                            self._versioned_base_url() + 'utils/runtime-config')

        if response.status_code != 200:
            raise CitrineException(response.text)
        self._accounts_service_v3 = response.json().get('accounts_service_v3', False)

    def _request_with_retry(self, method, uri, **kwargs):
        """Wrap a request with a try/except to retry when ConnectionErrors are seen."""
        # The urllib3 Retry object does not handle retries when ConnectionErrors
        # (or other similar errors) and raised.  Using a stale connection causes
        # these issues.  Retrying the request uses a new connection.  See PLA-3449/4183.
        try:
            response = self.request(method, uri, **kwargs)
        except self.retry_errs as e:
            logger.warning('{} seen, retrying request'.format(repr(e)))
            response = self.request(method, uri, **kwargs)

        return response

    def checked_request(self, method: str, path: str,
                        version: str = 'v1', **kwargs) -> requests.Response:
        """Check response status code and throw an exception if relevant."""
        logger.debug('BEGIN request details:')
        logger.debug('\tmethod: {}'.format(method))
        logger.debug('\tpath: {}'.format(path))
        logger.debug('\tversion: {}'.format(version))

        if self._is_access_token_expired():
            self._refresh_access_token()
            self._check_accounts_version()
        uri = self._versioned_base_url(version) + path.lstrip('/')

        logger.debug('\turi: {}'.format(uri))

        for k, v in kwargs.items():
            logger.debug('\t{}: {}'.format(k, v))
        logger.debug('END request details.')

        response = self._request_with_retry(method, uri, **kwargs)

        try:
            if response.status_code == 401 and response.json().get("reason") == "invalid-token":
                self._refresh_access_token()
                self._check_accounts_version()
                response = self._request_with_retry(method, uri, **kwargs)
        except AttributeError:
            # Catch AttributeErrors and log response
            # The 401 status will be handled further down
            logger.error("Failed to decode json from response: {}".format(response.text))
        except ValueError:
            # Ignore ValueErrors thrown by attempting to decode json bodies. This
            # might occur if we get a 401 response without a JSON body
            pass

        if 200 <= response.status_code <= 299:
            logger.info('%s %s %s', response.status_code, method, path)
            return response
        else:
            stacktrace = self._extract_response_stacktrace(response)
            if stacktrace is not None:
                logger.error('Response arrived with stacktrace:')
                logger.error(stacktrace)
            if response.status_code == 400:
                logger.error('%s %s %s', response.status_code, method, path)
                logger.error(response.text)
                raise BadRequest(path, response)
            elif response.status_code == 401:
                logger.error('%s %s %s', response.status_code, method, path)
                raise Unauthorized(path, response)
            elif response.status_code == 403:
                logger.error('%s %s %s', response.status_code, method, path)
                raise Unauthorized(path, response)
            elif response.status_code == 404:
                logger.error('%s %s %s', response.status_code, method, path)
                raise NotFound(path, response)
            elif response.status_code == 409:
                logger.debug('%s %s %s', response.status_code, method, path)
                raise Conflict(path, response)
            elif response.status_code == 425:
                logger.debug('%s %s %s', response.status_code, method, path)
                msg = 'Cant execute at this time. Try again later. Error: {}'.format(response.text)
                raise WorkflowNotReadyException(msg)
            else:
                logger.error('%s %s %s', response.status_code, method, path)
                raise CitrineException(response.text)

    @staticmethod
    def _extract_response_stacktrace(response: Response) -> Optional[str]:
        try:
            json_value = response.json()
            if isinstance(json_value, dict):
                return json_value.get('debug_stacktrace')
        except ValueError:
            pass
        return None

    def get_resource(self, path: str, **kwargs) -> dict:
        """GET a particular resource as JSON."""
        response = self.checked_get(path, **kwargs)
        return self._extract_response_json(path, response)

    def post_resource(self, path: str, json: dict, **kwargs) -> dict:
        """POST to a particular resource as JSON."""
        response = self.checked_post(path, json=json, **kwargs)
        return self._extract_response_json(path, response)

    def put_resource(self, path: str, json: dict, **kwargs) -> dict:
        """PUT data given by some JSON at a particular resource."""
        response = self.checked_put(path, json=json, **kwargs)
        return self._extract_response_json(path, response)

    def patch_resource(self, path: str, json: dict, **kwargs) -> dict:
        """PATCH data given by some JSON at a particular resource."""
        response = self.checked_patch(path, json=json, **kwargs)
        return self._extract_response_json(path, response)

    def delete_resource(self, path: str, **kwargs) -> dict:
        """DELETE a particular resource as JSON."""
        response = self.checked_delete(path, **kwargs)
        return self._extract_response_json(path, response)

    @staticmethod
    def _extract_response_json(path, response) -> dict:
        """Extract json from the response or log and return an empty dict if extraction fails."""
        extracted_response = {}
        try:
            if "application/json" in response.headers.get("Content-Type", ""):
                extracted_response = response.json()
            else:  # pragma: no cover
                logger.info(f"""Response at {path} with status code of {response.status_code}
                    lacked the required 'application/json' Content-Type in the header.""")

        except JSONDecodeError as err:
            logger.info('Response at path %s with status code %s failed json parsing with'
                        ' exception %s. Returning empty value.',
                        path,
                        response.status_code,
                        err.msg)

        return extracted_response

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

    def checked_post(self, path: str, json: dict, **kwargs) -> Response:
        """Execute a POST request to a URL and utilize error filtering on the response."""
        return self.checked_request('POST', path, json=json, **kwargs)

    def checked_put(self, path: str, json: dict, **kwargs) -> Response:
        """Execute a PUT request to a URL and utilize error filtering on the response."""
        return self.checked_request('PUT', path, json=json, **kwargs)

    def checked_patch(self, path: str, json: dict, **kwargs) -> Response:
        """Execute a PATCH request to a URL and utilize error filtering on the response."""
        return self.checked_request('PATCH', path, json=json, **kwargs)

    def checked_delete(self, path: str, **kwargs) -> Response:
        """Execute a DELETE request to a URL and utilize error filtering on the response."""
        return self.checked_request('DELETE', path, **kwargs)

    def checked_get(self, path: str, **kwargs) -> Response:
        """Execute a GET request to a URL and utilize error filtering on the response."""
        return self.checked_request('GET', path, **kwargs)


class BearerAuth(requests.auth.AuthBase):
    """A lightweight Auth class to support Bearer tokens."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        """Generate the appropriate Authorization header."""
        r.headers["Authorization"] = "Bearer " + self.token
        return r
