import json

import jwt
import pytest
import unittest

from citrine.exceptions import (
    NonRetryableException,
    WorkflowConflictException,
    WorkflowNotReadyException,
    RetryableException,
    BadRequest)

from datetime import datetime, timedelta
import pytz
import mock
import requests
import requests_mock
from citrine._session import Session
from citrine.exceptions import UnauthorizedRefreshToken, Unauthorized, NotFound
from tests.utils.session import make_fake_cursor_request_function


def refresh_token(expiration: datetime = None) -> dict:
    token = jwt.encode(
        payload={'exp': expiration.timestamp()},
        key='garbage'
    )
    return {'access_token': token.decode('utf-8')}


@pytest.fixture
def session():
    session = Session(
        refresh_token='12345',
        scheme='http',
        host='citrine-testing.fake'
    )
    # Default behavior is to *not* require a refresh - those tests can clear this out
    # As rule of thumb, we should be using freezegun or similar to never rely on the system clock
    # for these scenarios, but I thought this is light enough to postpone that for the time being
    session.access_token_expiration = datetime.utcnow() + timedelta(minutes=3)

    return session


def test_get_refreshes_token(session: Session):
    session.access_token_expiration = datetime.utcnow() - timedelta(minutes=1)
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))

    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        m.get('http://citrine-testing.fake/api/v1/foo', json={'foo': 'bar'})

        resp = session.get_resource('/foo')

    assert {'foo': 'bar'} == resp
    assert datetime(2019, 3, 14) == session.access_token_expiration


def test_get_refresh_token_failure(session: Session):
    session.access_token_expiration = datetime.utcnow() - timedelta(minutes=1)

    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', status_code=401)

        with pytest.raises(UnauthorizedRefreshToken):
            session.get_resource('/foo')


def test_get_no_refresh(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', json={'foo': 'bar'})
        resp = session.get_resource('/foo')

    assert {'foo': 'bar'} == resp


def test_get_not_found(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=404)
        with pytest.raises(NotFound):
            session.get_resource('/foo')


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
    def test_status_code_400(self, mock_request, _):
        resp = mock.Mock()
        resp.status_code = 400
        resp_json = {
            'code': 400,
            'message': 'a message',
            'validation_errors': [
                {
                    'failure_message': 'you have failed',
                },
            ],
        }
        resp.json = lambda: resp_json
        resp.text = json.dumps(resp_json)
        mock_request.return_value = resp
        with pytest.raises(BadRequest) as einfo:
            Session().checked_request('method', 'path')
        assert einfo.value.api_error.validation_errors[0].failure_message \
            == resp_json['validation_errors'][0]['failure_message']

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

    @mock.patch.object(Session, '_refresh_access_token')
    @mock.patch.object(requests.Session, 'request')
    def test_connection_error(self, mock_request, _):

        data = {'stuff': 'not_used'}
        call_count = 0

        # Simulate a request using a stale session that raises
        # a ConnectionError then works on the second call.
        def request_side_effect(method, uri):
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                raise requests.exceptions.ConnectionError
            else:
                return data

        mock_request.side_effect = request_side_effect
        resp = Session()._request_with_retry('method', 'path')

        assert resp == data


def test_post_refreshes_token_when_denied(session: Session):
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))

    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        m.register_uri('POST', 'http://citrine-testing.fake/api/v1/foo', [
            {'status_code': 401, 'json': {'reason': 'invalid-token'}},
            {'json': {'foo': 'bar'}}
        ])

        resp = session.post_resource('/foo', json={'data': 'hi'})

    assert {'foo': 'bar'} == resp
    assert datetime(2019, 3, 14) == session.access_token_expiration


def test_delete_unauthorized_without_json(session: Session):
    with requests_mock.Mocker() as m:
        m.delete('http://citrine-testing.fake/api/v1/bar/something', status_code=401)

        with pytest.raises(Unauthorized):
            session.delete_resource('/bar/something')


def test_failed_put_with_stacktrace(session: Session):
    with mock.patch("time.sleep", return_value=None):
        with requests_mock.Mocker() as m:
            m.put(
                'http://citrine-testing.fake/api/v1/bad-endpoint',
                status_code=500,
                json={'debug_stacktrace': 'blew up!'}
            )

            with pytest.raises(Exception) as e:
                session.put_resource('/bad-endpoint', json={})

        assert '{"debug_stacktrace": "blew up!"}' == str(e.value)


def test_cursor_paged_resource():
    full_result_set = list(range(26))

    fake_request = make_fake_cursor_request_function(full_result_set)

    # varying page size should not affect final result
    assert list(Session.cursor_paged_resource(fake_request, 'foo', forward=True, per_page=10)) == full_result_set
    assert list(Session.cursor_paged_resource(fake_request, 'foo', forward=True, per_page=26)) == full_result_set
    assert list(Session.cursor_paged_resource(fake_request, 'foo', forward=True, per_page=40)) == full_result_set


def test_bad_json_response(session: Session):
    with requests_mock.Mocker() as m:
        m.delete('http://citrine-testing.fake/api/v1/bar/something', status_code=200)
        response_json = session.delete_resource('/bar/something')
        assert response_json == {}


def test_good_json_response(session: Session):
    with requests_mock.Mocker() as m:
        json_to_validate = {"bar": "something"}
        m.put('http://citrine-testing.fake/api/v1/bar/something', status_code=200, json=json_to_validate)
        response_json = session.put_resource('bar/something', {"ignored": "true"})
        assert response_json == json_to_validate
