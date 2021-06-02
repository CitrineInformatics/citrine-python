from citrine import Citrine


def test_citrine_creation():
    assert '1234' == Citrine(api_key='1234', host='citrine.io').session.refresh_token


def test_citrine_project_session():
    citrine = Citrine(api_key='foo', host='bar')
    assert citrine.session == citrine.projects.session


def test_citrine_user_session():
    citrine = Citrine(api_key='foo', host='bar')
    assert citrine.session == citrine.users.session
