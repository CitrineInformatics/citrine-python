from citrine import Citrine


def test_citrine_creation():
    assert '1234' == Citrine('1234').session.refresh_token


def test_citrine_project_session():
    citrine = Citrine('foo')
    assert citrine.session == citrine.projects.session


def test_citrine_user_session():
    citrine = Citrine('foo')
    assert citrine.session == citrine.users.session
