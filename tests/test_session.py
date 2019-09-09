import pytest
import unittest

from citrine.exceptions import (
    NonRetryableException,
    NotFound,
    RetryableException,
    Unauthorized,
    WorkflowConflictException,
    WorkflowNotReadyException,
)
from citrine._session import Session

import mock
import requests


class SessionTests(unittest.TestCase):
    @mock.patch.object(Session, '_refresh_access_token')
    @mock.patch.object(requests.Session, 'request')
    def test_status_code_409(self, mock_request, _):
        resp = mock.Mock()
        resp.status_code = 409
        mock_request.return_value = resp
        with pytest.raises(NonRetryableException):
            Session().checked_request('method', 'path')
        with pytest.raises(WorkflowConflictException):
            Session().checked_request('method', 'path')

    @mock.patch.object(Session, '_refresh_access_token')
    @mock.patch.object(requests.Session, 'request')
    def test_status_code_425(self, mock_request, _):
        resp = mock.Mock()
        resp.status_code = 425
        mock_request.return_value = resp
        with pytest.raises(RetryableException):
            Session().checked_request('method', 'path')
        with pytest.raises(WorkflowNotReadyException):
            Session().checked_request('method', 'path')

    @mock.patch.object(Session, '_refresh_access_token')
    @mock.patch.object(requests.Session, 'request')
    def test_status_code_401(self, mock_request, _):
        resp = mock.Mock()
        resp.status_code = 401
        mock_request.return_value = resp
        with pytest.raises(NonRetryableException):
            Session().checked_request('method', 'path')
        with pytest.raises(Unauthorized):
            Session().checked_request('method', 'path')

    @mock.patch.object(Session, '_refresh_access_token')
    @mock.patch.object(requests.Session, 'request')
    def test_status_code_404(self, mock_request, _):
        resp = mock.Mock()
        resp.status_code = 404
        mock_request.return_value = resp
        with pytest.raises(NonRetryableException):
            Session().checked_request('method', 'path')
        with pytest.raises(NotFound):
            Session().checked_request('method', 'path')
