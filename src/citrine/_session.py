from os import environ
from typing import Optional
from logging import getLogger
from datetime import datetime, timedelta
from citrine.exceptions import (
    NotFound,
    Unauthorized,
    UnauthorizedRefreshToken,
    WorkflowConflictException,
    WorkflowNotReadyException,
)

import jwt
import requests


# Choose a 5 second buffer so that there's no chance of the access token
# expiring during the check for expiration
EXPIRATION_BUFFER_MILLIS: timedelta = timedelta(milliseconds=5000)


class Session(requests.Session):
    """Wrapper around requests.Session that is both refresh-token and schema aware."""

    def __init__(self,
                 refresh_token: str = environ.get('CITRINE_API_TOKEN'),
                 scheme: str = 'https',
                 host: str = 'citrine.io',
                 port: Optional[str] = None):
        super().__init__()
        self.logger = getLogger(__name__)
        self.scheme: str = scheme
        self.authority = ':'.join([host, port or ''])
        self.refresh_token: str = refresh_token
        self.access_token: Optional[str] = None
        self.access_token_expiration: datetime = datetime.utcnow()

        # Following scheme:[//authority]path[?query][#fragment] (https://en.wikipedia.org/wiki/URL)
        self.base_url = '{}://{}/api/v1/'.format(self.scheme, self.authority)
        self.headers.update({"Content-Type": "application/json"})

    def _is_access_token_expired(self):
        return self.access_token_expiration - EXPIRATION_BUFFER_MILLIS <= datetime.utcnow()

    def _refresh_access_token(self) -> None:
        """Optionally refresh our access token (if the previous one is about to expire)."""
        data = {'refresh_token': self.refresh_token}
        response = super().request('POST', self.base_url + 'tokens/refresh', json=data)
        if response.status_code != 200:
            raise UnauthorizedRefreshToken()
        self.access_token = response.json()['access_token']
        self.access_token_expiration = datetime.utcfromtimestamp(
            jwt.decode(self.access_token, verify=False)['exp']
        )

    def checked_request(self, method: str, path: str, *args, **kwargs) -> requests.Response:
        """Check response status code and throw an exception if relevant."""
        if self._is_access_token_expired():
            self._refresh_access_token()
        uri = self.base_url + path.lstrip('/')
        response = super().request(method, uri, *args, **kwargs)

        try:
            if response.status_code == 401 and response.json().get("reason") == "invalid-token":
                self._refresh_access_token()
                response = super().request(method, uri, *args, **kwargs)
        except ValueError:
            # Ignore ValueErrors thrown by attempting to decode json bodies. This
            # might occur if we get a 401 response without a JSON body
            pass

        # TODO: More substantial/careful error handling
        if 200 <= response.status_code <= 299:
            self.logger.info('%s %s %s', response.status_code, method, path)
            return response
        else:
            try:
                stacktrace = response.json().get('debug_stacktrace')
                if stacktrace:
                    self.logger.error('Response arrived with stacktrace:')
                    self.logger.error(stacktrace)
            except ValueError:
                pass
            if response.status_code == 401:
                self.logger.error('%s %s %s', response.status_code, method, path)
                raise Unauthorized(path)
            elif response.status_code == 404:
                self.logger.warning('%s %s %s', response.status_code, method, path)
                raise NotFound(path)
            elif response.status_code == 409:
                self.logger.warning('%s %s %s', response.status_code, method, path)
                raise WorkflowConflictException(response.text)
            elif response.status_code == 425:
                self.logger.warning('%s %s %s', response.status_code, method, path)
                msg = 'Cant execute at this time. Try again later. Error: {}'.format(response.text)
                raise WorkflowNotReadyException(msg)
            else:
                self.logger.error('%s %s %s', response.status_code, method, path)
                raise Exception(response.text)

    def get_resource(self, path: str, *args, **kwargs) -> dict:
        """GET a particular resource as JSON."""
        # TODO: Fix this return value (possibly list)
        return self.checked_request('GET', path, *args, **kwargs).json()

    def post_resource(self, path: str, json: dict, *args, **kwargs) -> dict:
        """POST to a particular resource as JSON."""
        return self.checked_request('POST', path, *args, json=json, **kwargs).json()

    def delete_resource(self, path: str) -> dict:
        """DELETE a particular resource as JSON."""
        return self.checked_request('DELETE', path).json()
