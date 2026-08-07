from citrine.resources.project_roles import ROLES
from citrine.resources.user import User


class ProjectMember:
    """A Member of a Project."""

    def __init__(
        self,
        *,
        user: User,
        project: "Project",  # noqa: F821
        role: ROLES,
    ):
        self.user: User = user
        # To avoid circular dependency, use forward-reference for type definition
        # https://www.python.org/dev/peps/pep-0484/#forward-references
        self.project: Project = project  # noqa: F821
        self.role: ROLES = role

    def __str__(self):
        return (
            f"<ProjectMember {self.user.screen_name!r} is {self.role!s} of {self.project.name!r}>"
        )
