"""Resources that represent both individual and collections of teams."""
from typing import Optional, Union, List, Iterable, Tuple
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.resources.user import User


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

    name = properties.String('name')
    description = properties.Optional(properties.String(), 'description')
    uid = properties.Optional(properties.UUID(), 'id')
    created_at = properties.Optional(properties.Datetime(), 'created_at')  # TODO does a team have this??

    def __init__(self,
                 name: str,
                 *,
                 description: Optional[str] = None,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: Optional[str] = description
        self.session: Session = session

    def __str__(self):
        return '<Team {!r}>'.format(self.name)

    def _path(self):
        return format_escaped_url('/teams/{team_id}', team_id=self.uid)

    def list_members(self) -> List[User]:
        raise NotImplementedError("TODO")

    def remove_user(self, user_id: Union[str, UUID]) -> List[User]:
        raise NotImplementedError("TODO")

    def add_user(self, user_id: Union[str, UUID]) -> List[User]:
        raise NotImplementedError("TODO")

    def update_user_action(self, user_id: Union[str, UUID], actions) -> List[User]:
        raise NotImplementedError("TODO")

    def share(self, asset_id: Union[str, UUID], team_id) -> List[User]:
        raise NotImplementedError("TODO")


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

    def register(self, name: str, *, description: Optional[str] = None) -> Team:
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
