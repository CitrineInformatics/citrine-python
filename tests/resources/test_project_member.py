import pytest

from citrine.resources.project import Project
from citrine.resources.project_member import ProjectMember
from citrine.resources.project_roles import MEMBER
from citrine.resources.user import User
from tests.utils.factories import ProjectDataFactory, UserDataFactory


@pytest.fixture
def project() -> Project:
    return Project.build(ProjectDataFactory())


@pytest.fixture
def user() -> User:
    return User.build(UserDataFactory())


@pytest.fixture()
def project_member(user, project) -> ProjectMember:
    return ProjectMember(user=user, project=project, role=MEMBER)


def test_string_representation(project_member):
    assert project_member.__str__() == "<ProjectMember '{}' is MEMBER of '{}'>"\
        .format(project_member.user.screen_name, project_member.project.name)
