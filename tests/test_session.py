import json

import jwt
import pytest
import unittest

from citrine.exceptions import (
    BadRequest,
    CitrineException,
    Conflict,
    NonRetryableException,
    WorkflowNotReadyException,
    RetryableException)

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
    return {'access_token': token}


@pytest.fixture
def session():
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))
    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
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


def test_session_signature(monkeypatch):
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))
    with requests_mock.Mocker() as m:
        m.post('ftp://citrine-testing.fake:8080/api/v1/tokens/refresh', json=token_refresh_response)

        assert '1234' == Session(refresh_token='1234',
                                 scheme='ftp',
                                 host='citrine-testing.fake',
                                 port="8080").refresh_token

    # Validate defaults
    with requests_mock.Mocker() as m:
        patched_key = "5678"
        patched_host = "monkeypatch.citrine-testing.fake"
        monkeypatch.setenv("CITRINE_API_KEY", patched_key)
        monkeypatch.setenv("CITRINE_API_HOST", patched_host)
        m.post(f'https://{patched_host}/api/v1/tokens/refresh', json=token_refresh_response)

        assert patched_key == Session().refresh_token
        assert patched_key == Session(refresh_token=patched_key).refresh_token
        monkeypatch.delenv("CITRINE_API_KEY")
        assert Session().refresh_token is None

    monkeypatch.delenv("CITRINE_API_HOST")
    with pytest.raises(ValueError):
        Session()


def test_get_refreshes_token(session: Session):
    session.access_token_expiration = datetime.utcnow() - timedelta(minutes=1)
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))

    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        m.get('http://citrine-testing.fake/api/v1/foo',
              json={'foo': 'bar'},
              headers={'content-type': "application/json"})

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
        m.get('http://citrine-testing.fake/api/v1/foo', json={'foo': 'bar'}, headers={'content-type': "application/json"})
        resp = session.get_resource('/foo')

    assert {'foo': 'bar'} == resp


def test_get_not_found(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=404)
        with pytest.raises(NotFound):
            session.get_resource('/foo')


def test_status_code_409(session: Session):
    with requests_mock.Mocker() as m:
        url = '/foo'
        conflict_message = 'you have a conflict'
        resp_json = {
            'code': 409,
            'message': 'a message',
            'validation_errors': [{'failure_message': conflict_message}]
        }
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=409, json=resp_json)
        with pytest.raises(Conflict) as einfo:
            session.get_resource(url)

        assert getattr(einfo.value, "url", None) == url
        assert conflict_message in str(einfo.value)
        assert "409" in str(einfo.value)


def test_status_code_425(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=425)
        with pytest.raises(RetryableException):
            session.get_resource('/foo')
        with pytest.raises(WorkflowNotReadyException):
            session.get_resource('/foo')


def test_status_code_400(session: Session):
    with requests_mock.Mocker() as m:
        resp_json = {
            'code': 400,
            'message': 'a message',
            'validation_errors': [
                {
                    'failure_message': 'you have failed',
                },
            ],
        }
        m.get('http://citrine-testing.fake/api/v1/foo',
              status_code=400,
              json=resp_json
              )
        with pytest.raises(BadRequest) as einfo:
            session.get_resource('/foo')
        assert einfo.value.api_error.validation_errors[0].failure_message \
               == resp_json['validation_errors'][0]['failure_message']


def test_status_code_401(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=401)
        with pytest.raises(NonRetryableException):
            session.get_resource('/foo')
        with pytest.raises(Unauthorized):
            session.get_resource('/foo')


def test_status_code_404(session: Session):
    with requests_mock.Mocker() as m:
        m.get('http://citrine-testing.fake/api/v1/foo', status_code=404)
        with pytest.raises(NonRetryableException):
            session.get_resource('/foo')


def test_connection_error(session: Session):
    data = {'stuff': 'not_used'}

    # Simulate a request using a stale session that raises
    # a ConnectionError then works on the second call.
    with requests_mock.Mocker() as m:
        m.register_uri('GET',
                       'http://citrine-testing.fake/api/v1/foo',
                       [{'exc': requests.exceptions.ConnectionError},
                        {'json': data, 'status_code': 200, 'headers': {'content-type': "application/json"}}])

        resp = session.get_resource('/foo')
        assert resp == data


def test_post_refreshes_token_when_denied(session: Session):
    token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))

    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        m.register_uri('POST', 'http://citrine-testing.fake/api/v1/foo', [
            {'status_code': 401, 'json': {'reason': 'invalid-token'}},
            {'json': {'foo': 'bar'}, 'headers': {'content-type': "application/json"}}
        ])

        resp = session.post_resource('/foo', json={'data': 'hi'})

    assert {'foo': 'bar'} == resp
    assert datetime(2019, 3, 14) == session.access_token_expiration


# this test exists to provide 100% coverage for the legacy 401 status on Unauthorized responses
def test_delete_unauthorized_without_json_legacy(session: Session):
    with requests_mock.Mocker() as m:
        m.delete('http://citrine-testing.fake/api/v1/bar/something', status_code=401)

        with pytest.raises(Unauthorized):
            session.delete_resource('/bar/something')


def test_delete_unauthorized_with_str_json_legacy(session: Session):
    with requests_mock.Mocker() as m:
        m.delete(
            'http://citrine-testing.fake/api/v1/bar/something',
            status_code=401,
            json='an error string'
        )

        with pytest.raises(Unauthorized):
            session.delete_resource('/bar/something')


def test_delete_unauthorized_without_json(session: Session):
    with requests_mock.Mocker() as m:
        m.delete('http://citrine-testing.fake/api/v1/bar/something', status_code=403)

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
        m.delete('http://citrine-testing.fake/api/v1/bar/something',
                 status_code=200,
                 headers={'content-type': "application/json"})
        response_json = session.delete_resource('/bar/something')
        assert response_json == {}


def test_good_json_response(session: Session):
    with requests_mock.Mocker() as m:
        json_to_validate = {"bar": "something"}
        m.put('http://citrine-testing.fake/api/v1/bar/something',
              status_code=200,
              json=json_to_validate,
              headers={'content-type': "application/json"})
        response_json = session.put_resource('bar/something', {"ignored": "true"})
        assert response_json == json_to_validate


def test_patch(session: Session):
    with requests_mock.Mocker() as m:
        json_to_validate = {"bar": "something"}
        m.patch('http://citrine-testing.fake/api/v1/bar/something',
                status_code=200,
                json=json_to_validate,
                headers={'content-type': "application/json"})
        response_json = session.patch_resource('bar/something', {"ignored": "true"})
        assert response_json == json_to_validate
