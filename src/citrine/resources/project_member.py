from citrine.resources.project_roles import ROLES
from citrine.resources.user import User


class ProjectMember:
    """A Member of a Project."""

    def __init__(self,
                 user: User,
                 project: 'Project',
                 role: ROLES):
        self.user: User = user
        self.project: 'Project' = project
        self.role: ROLES = role

    def __str__(self):
        return '<ProjectMember {!r} is {!s} of {!r}>'\
            .format(self.user.screen_name, self.role, self.project.name)
