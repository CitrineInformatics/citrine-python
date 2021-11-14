"""Resources that represent both individual and collections of teams."""
from typing import Optional, Union, List
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url

WRITE = "WRITE"
READ = "READ"
SHARE = "SHARE"
ACTIONS = Union[WRITE, READ, SHARE]


class TeamMember:
    """A Member of a Team."""

    def __init__(self,
                 *,
                 id: UUID,
                 screen_name: str,
                 email: str,
                 is_admin: bool,
                 team: 'Team',  # noqa: F821
                 actions: ACTIONS):
        self.id = id
        self.screen_name = screen_name
        self.email = email
        self.is_admin = is_admin
        self.team: 'Team' = team  # noqa: F821
        self.actions: ACTIONS = actions

    def __str__(self):
        return f'<TeamMember {self.screen_name} is MEMBER of {self.team.name}>'


class Team(Resource['Team']):
    """
    A Citrine Team.

    A Team is a collection of projects and resources.

    Parameters
    ----------
    name: str
        Name of the team.
    description: str
        Long-form description of the team.
    session: Session, optional
        The Citrine session used to connect to the database.

    Attributes
    ----------
    uid: UUID
        Unique uuid4 identifier of this team.
    created_at: int
        Time the team was created, in seconds since epoch.

    """

    _response_key = 'team'
    _resource_type = ResourceTypeEnum.TEAM
    _api_version = "v3"

    name = properties.String('name')
    description = properties.Optional(properties.String(), 'description')
    uid = properties.Optional(properties.UUID(), 'id')
    created_at = properties.Optional(properties.Datetime(), 'created_at')

    def __init__(self,
                 name: str,
                 *,
                 description: str = "",
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.session: Session = session

    def __str__(self):
        return '<Team {!r}>'.format(self.name)

    def _path(self):
        return format_escaped_url('/teams/{team_id}', team_id=self.uid)

    def list_members(self) -> List[TeamMember]:
        members = self.session.get_resource(self._path() + "/users",
                                            version=self._api_version)["users"]
        return [TeamMember(id=m["id"], screen_name=m["screen_name"], email=m["email"],
                is_admin=m["is_admin"], team=self, actions=m["actions"]) for m in members]

    def remove_user(self, user_id: Union[str, UUID]) -> bool:
        self.session.checked_post(self._path() + "/users/batch-remove",
                                  json={"ids": [str(user_id)]}, version=self._api_version)
        return True  # TODO fix this and project instances of this

    def add_user(self, user_id: Union[str, UUID], actions: ACTIONS = None) -> bool:
        if actions is None:
            actions = [READ]
        return self.update_user_action(user_id, actions)

    def update_user_action(self, user_id: Union[str, UUID], actions: List[ACTIONS]) -> bool:
        self.session.checked_put(self._path() + "/users", version=self._api_version,
                                 json={'id': str(user_id), "actions": actions})
        return True

    def share(self, *,
              resource: Resource,
              target_team_id: Union[str, UUID]) -> bool:
        resource_access = resource.access_control_dict()
        payload = {
            "resource_type": resource_access["type"],
            "resource_id": resource_access["id"],
            "target_team_id": str(target_team_id)
        }
        self.session.checked_post(self._path() + "/shared-resources",
                                  version=self._api_version, json=payload)
        return True

    def un_share(self, resource: Resource, target_team_id: Union[str, UUID]) -> bool:
        resource_type = resource.access_control_dict()["type"]
        resource_id = resource.access_control_dict()["id"]
        self.session.checked_delete(
            self._path() + f"/shared-resources/{resource_type}/{resource_id}",
            version=self._api_version,
            json={"target_team_id": str(target_team_id)}
        )
        return True


class TeamCollection(Collection[Team]):
    """
    Represents the collection of all teams as well as the resources belonging to it.

    Parameters
    ----------
    session: Session, optional
        The Citrine session used to connect to the database.

    """

    _path_template = '/teams'
    _individual_key = 'team'
    _collection_key = 'teams'
    _resource = Team
    _api_version = "v3"

    def __init__(self, session: Session):
        self.session = session

    def build(self, data) -> Team:
        """
        Build an individual team from a dictionary.

        Parameters
        ----------
        data: dict
            A dictionary representing the team.

        Return
        -------
        Team
            The team created from data.

        """
        team = Team.build(data)
        team.session = self.session
        return team

    def update(self, team: Team) -> Team:
        """
        Update a particular team.

        You can only update the name and/or description.
        """
        url = self._get_path(team.uid)
        updated = self.session.patch_resource(url, team.dump(), version=self._api_version)
        data = updated[self._individual_key]
        return self.build(data)

    def register(self, name: str, *, description: str = "") -> Team:
        """
        Create and upload new team.

        Parameters
        ----------
        name: str
            Name of the team to be created.
        description: str
            Long-form description of the team to be created.

        """
        return super().register(Team(name, description=description))
