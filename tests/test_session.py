import jwt
import pytest
from datetime import datetime, timedelta
import pytz
import requests_mock
from citrine._session import Session
from citrine.exceptions import UnauthorizedRefreshToken, Unauthorized, NotFound


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
    with requests_mock.Mocker() as m:
        m.put(
            'http://citrine-testing.fake/api/v1/bad-endpoint',
            status_code=500,
            json={'debug_stacktrace': 'blew up!'}
        )

        with pytest.raises(Exception) as e:
            session.put_resource('/bad-endpoint', json={})

    assert '{"debug_stacktrace": "blew up!"}' == str(e.value)
