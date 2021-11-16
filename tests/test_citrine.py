import platform

import pytest

from citrine import Citrine
from citrine.exceptions import AccountsV3Exception
from tests.utils.session import FakeSession


def test_citrine_creation():
    assert '1234' == Citrine(api_key='1234', host='citrine.io').session.refresh_token


def test_citrine_project_session():
    citrine = Citrine(api_key='foo', host='bar')
    assert citrine.session == citrine.projects.session


def test_citrine_user_session():
    citrine = Citrine(api_key='foo', host='bar')
    assert citrine.session == citrine.users.session


def test_citrine_team_session():
    citrine = Citrine(api_key='foo', host='bar')
    citrine.session = FakeSession(accounts_v3=False)  # use a fake session
    with pytest.raises(AccountsV3Exception):
        citrine.teams


def test_citrine_team_session_v3():
    citrine = Citrine(api_key='foo', host='bar')
    citrine.session = FakeSession(accounts_v3=True)  # use the fake v3 session
    assert citrine.session == citrine.teams.session


def test_citrine_user_agent():
    citrine = Citrine(api_key='foo', host='bar')
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
