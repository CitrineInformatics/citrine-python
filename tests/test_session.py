import pytest
import unittest

from citrine.exceptions import (
    NonRetryableException,
    NotFound,
    Unauthorized,
)
from citrine._session import Session

import mock
import requests


class SessionTests(unittest.TestCase):
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

    @mock.patch.object(Session, '_refresh_access_token')
    def test_extract_response_stacktrace(self, _):
        # TODO: make this weak test cheat less
        err_json_dict_resp = mock.Mock()
        err_json_dict_resp.json = mock.Mock()
        err_json_dict_resp.json.return_value = {'debug_stacktrace': 'foo'}
        self.assertEqual(Session()._extract_response_stacktrace(err_json_dict_resp), 'foo')
        err_json_dict_resp = mock.Mock()
        err_json_dict_resp.json = mock.Mock()
        err_json_dict_resp.json.return_value = 'a string deserialized from json'
        self.assertIsNone(Session()._extract_response_stacktrace(err_json_dict_resp))

