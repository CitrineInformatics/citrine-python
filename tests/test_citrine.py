import platform
from datetime import datetime

import jwt
import pytest
import pytz
import requests_mock

from citrine import Citrine


def refresh_token(expiration: datetime = None) -> dict:
    token = jwt.encode(
        payload={'exp': expiration.timestamp()},
        key='garbage'
    )
    return {'access_token': token}


token_refresh_response = refresh_token(datetime(2019, 3, 14, tzinfo=pytz.utc))


def test_citrine_creation():
    with requests_mock.Mocker() as m:
        m.post('https://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)

        assert '1234' == Citrine(api_key='1234', host='citrine-testing.fake').session.refresh_token


def test_citrine_signature(monkeypatch):
    with requests_mock.Mocker() as m:
        m.post('http://citrine-testing.fake:8080/api/v1/tokens/refresh', json=token_refresh_response)

        assert '1234' == Citrine(api_key='1234',
                                 scheme='http',
                                 host='citrine-testing.fake',
                                 port="8080").session.refresh_token

    # Validate defaults
    with requests_mock.Mocker() as m:
        patched_key = "5678"
        patched_host = "monkeypatch.citrine-testing.fake"
        monkeypatch.setenv("CITRINE_API_KEY", patched_key)
        monkeypatch.setenv("CITRINE_API_HOST", patched_host)
        m.post(f'https://{patched_host}/api/v1/tokens/refresh', json=token_refresh_response)

        assert patched_key == Citrine().session.refresh_token
        assert patched_key == Citrine(api_key=patched_key).session.refresh_token
        monkeypatch.delenv("CITRINE_API_KEY")
        assert Citrine().session.refresh_token is None

    monkeypatch.delenv("CITRINE_API_HOST")
    with pytest.raises(ValueError):
        Citrine()


def test_citrine_project_session():
    with requests_mock.Mocker() as m:
        m.post('https://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)

        citrine = Citrine(api_key='foo', host='citrine-testing.fake')

    assert citrine.session == citrine.projects.session


def test_citrine_user_session():
    with requests_mock.Mocker() as m:
        m.post('https://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        citrine = Citrine(api_key='foo', host='citrine-testing.fake')
    assert citrine.session == citrine.users.session


def test_citrine_team_session():
    with requests_mock.Mocker() as m:
        m.post('https://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        citrine = Citrine(api_key='foo', host='citrine-testing.fake')
    assert citrine.session == citrine.teams.session


def test_citrine_user_agent():
    with requests_mock.Mocker() as m:
        m.post('https://citrine-testing.fake/api/v1/tokens/refresh', json=token_refresh_response)
        citrine = Citrine(api_key='foo', host='citrine-testing.fake')

    agent_parts = citrine.session.headers['User-Agent'].split()
    python_impls = {'CPython', 'IronPython', 'Jython', 'PyPy'}
    expected_products = {'python-requests', 'citrine-python'}

    for product in agent_parts:
        product_name, product_version = product.split('/')
        assert product_name in {*python_impls, *expected_products}

        if product_name in python_impls:
            assert product_version == platform.python_version()
        else:
            # Check that the version is major.minor.patch but don't
            # enforce them to be ints.  It's common to see strings used
            # as the patch version
            assert len(product_version.split('.')) == 3
