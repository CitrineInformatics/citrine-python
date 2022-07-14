"""Resources that represent both individual and collections of teams."""
from typing import Optional, Union, List
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.resources import ProjectCollection
from citrine.resources.user import User, UserCollection

WRITE = "WRITE"
READ = "READ"
SHARE = "SHARE"
TEAM_ACTIONS = Union[WRITE, READ, SHARE]


class TeamMember:
    """A Member of a Team."""

    def __init__(self,
                 *,
                 user: User,
                 team: 'Team',  # noqa: F821
                 actions: List[TEAM_ACTIONS]):
        self.user = user
        self.team: 'Team' = team  # noqa: F821
        self.actions: List[TEAM_ACTIONS] = actions

    def __str__(self):
        return '<TeamMember {!r} can {!s} in {!r}>' \
            .format(self.user.screen_name, self.actions, self.team.name)


class TeamResourceIDs:
    """
    A Citrine Team Resource IDs class.

    This class is used to list the unique IDs for specific resource
    types published in a single team and therefore available to be pulled
    in by all projects.

    Parameters
    ----------
    team_id: str or uuid
        ID of the team.
    resource_type: str
        The resource type to list, one of DATASET/MODULE/TABLE/TABLE_DEFINITION

    """

    _api_version = "v3"

    def __init__(self,
                 session: Session,
                 team_id: Union[str, UUID],
                 resource_type: str) -> None:
        self.session = session
        self.team_id = team_id
        self.resource_type = resource_type

    def _path(self) -> str:
        return format_escaped_url(f'/teams/{self.team_id}')

    def _list_ids(self, action: str) -> List[str]:
        query_params = {"domain": self._path(), "action": action}
        return self.session.get_resource(f"/{self.resource_type}/authorized-ids",
                                         params=query_params,
                                         version=self._api_version)['ids']

    def list_readable(self):
        """
        List IDs of the published resources with READ access.

        Returns
        -------
        List[str]
            Returns a list of string UUIDs for each resource

        """
        return self._list_ids(action=READ)

    def list_writeable(self):
        """
        List IDs of the published resources with WRITE access.

        Returns
        -------
        List[str]
            Returns a list of string UUIDs for each resource

        """
        return self._list_ids(action=WRITE)

    def list_shareable(self):
        """
        List IDs of the published resources with SHARE access.

        Returns
        -------
        List[str]
            Returns a list of string UUIDs for each resource

        """
        return self._list_ids(action=SHARE)


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
    name: str
        Name of the Team
    description: str
        Description of the Team

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
        """
        List all of the members in the current team.

        Requires admin privileges.

        Returns
        -------
        List[TeamMember]
            The members of the current team

        """
        members = self.session.get_resource(self._path() + "/users",
                                            version=self._api_version)["users"]
        return [TeamMember(user=User.build(m), team=self, actions=m["actions"]) for m in members]

    def get_member(self, user_id: Union[str, UUID, User]) -> TeamMember:
        """
        Get a particular member in the current team.

        May require admin privileges depending on which user is being requested.

        Parameters
        ----------
        user_id: str or uuid
            The id of the user to remove from the team

        Returns
        -------
        TeamMember
            The requested team member

        """
        if isinstance(user_id, User):
            user_id = user_id.uid
        path = self._path() + format_escaped_url('/users/{user_id}', user_id=user_id)
        member = self.session.get_resource(path=path, version=self._api_version)["user"]
        return TeamMember(user=User.build(member), team=self, actions=member["actions"])

    def me(self) -> TeamMember:
        """
        Get the member for the current user.

        Returns
        -------
        TeamMember
            The TeamMember object representing the current user

        """
        me = UserCollection(self.session).me()
        return self.get_member(me)

    def remove_user(self, user_id: Union[str, UUID, User]) -> bool:
        """
        Remove a User from a Team.

        Requires admin privileges.

        Parameters
        ----------
        user_id: User, str or uuid
            The id of the user to remove from the team

        Returns
        -------
        bool
            Returns ``True`` if user successfully removed

        """
        if isinstance(user_id, User):
            user_id = user_id.uid
        self.session.checked_post(self._path() + "/users/batch-remove",
                                  json={"ids": [str(user_id)]}, version=self._api_version)
        return True  # note: only get here if checked_post doesn't raise error

    def add_user(self,
                 user_id: Union[str, UUID, User],
                 *,
                 actions: Optional[List[TEAM_ACTIONS]] = None) -> bool:
        """
        Add a User to a Team.

        Requires admin privileges.

        If no actions are specified, adds User with ``READ`` action to the Team.

        Use the `update_user_action` method to change a User's actions.

        Parameters
        ----------
        user_id: User, str or uuid
            The id of the user to add to the team
        actions: list of TEAM_ACTIONS
            The actions to give the new user in this team
            The options are: WRITE, READ, SHARE
            defaults to READ

        Returns
        -------
        bool
            Returns ``True`` if user successfully added

        """
        if isinstance(user_id, User):
            user_id = user_id.uid
        if actions is None:
            actions = [READ]
        return self.update_user_action(user_id, actions=actions)

    def update_user_action(self,
                           user_id: Union[str, UUID, User],
                           *,
                           actions: List[TEAM_ACTIONS]) -> bool:
        """
        Overwrites a User's action permissions in the Team.

        Requires admin privileges.

        Parameters
        ----------
        user_id: User, str or uuid
            The id of the user to add to the team
        actions: list of TEAM_ACTIONS
            The actions to give the new user in this team
            The options are: WRITE, READ, SHARE

        Returns
        -------
        bool
            Returns ``True`` if user successfully added

        """
        if isinstance(user_id, User):
            user_id = user_id.uid
        self.session.checked_put(self._path() + "/users", version=self._api_version,
                                 json={'id': str(user_id), "actions": actions})
        return True

    def share(self,
              *,
              resource: Resource,
              target_team_id: Union[str, UUID, "Team"]) -> bool:
        """
        Share a resource with another team.

        Requires SHARE action.

        Parameters
        ----------
        resource: Resource
            The resource owned by this team, which will be shared
        target_team_id: Union[str, UUID, Team]
            The id of the team with which to share the resource

        Returns
        -------
        bool
            Returns ``True`` if resource successfully shared

        """
        if isinstance(target_team_id, Team):
            target_team_id = target_team_id.uid
        resource_access = resource.access_control_dict()
        payload = {
            "resource_type": resource_access["type"],
            "resource_id": resource_access["id"],
            "target_team_id": str(target_team_id)
        }
        self.session.checked_post(self._path() + "/shared-resources",
                                  version=self._api_version, json=payload)
        return True

    def un_share(self, *, resource: Resource, target_team_id: Union[str, UUID, "Team"]) -> bool:
        """
        Revoke the share of a particular resource to a secondary team.

        Requires SHARE action.

        Parameters
        ----------
        resource: Resource
            The resource owned by this team, which will be un-shared
        target_team_id: Union[str, UUID, Team]
            The id of the team which should not have access to the resource

        Returns
        -------
        bool
            Returns ``True`` if resource successfully un-shared

        """
        if isinstance(target_team_id, Team):
            target_team_id = target_team_id.uid
        resource_type = resource.access_control_dict()["type"]
        resource_id = resource.access_control_dict()["id"]
        self.session.checked_delete(
            self._path() + f"/shared-resources/{resource_type}/{resource_id}",
            version=self._api_version,
            json={"target_team_id": str(target_team_id)}
        )
        return True

    @property
    def projects(self) -> ProjectCollection:
        """Return a resource representing all visible projects in this team."""
        return ProjectCollection(self.session, team_id=self.uid)

    @property
    def dataset_ids(self) -> TeamResourceIDs:
        """Return a TeamResourceIDs instance for listing published dataset IDs."""
        return TeamResourceIDs(session=self.session,
                               team_id=self.uid,
                               resource_type=ResourceTypeEnum.DATASET.value)

    @property
    def module_ids(self) -> TeamResourceIDs:
        """Return a TeamResourceIDs instance for listing published module IDs."""
        return TeamResourceIDs(session=self.session,
                               team_id=self.uid,
                               resource_type=ResourceTypeEnum.MODULE.value)

    @property
    def table_ids(self) -> TeamResourceIDs:
        """Return a TeamResourceIDs instance for listing published table IDs."""
        return TeamResourceIDs(session=self.session,
                               team_id=self.uid,
                               resource_type=ResourceTypeEnum.TABLE.value)

    @property
    def table_definition_ids(self) -> TeamResourceIDs:
        """Return a TeamResourceIDs instance for listing published table definition IDs."""
        return TeamResourceIDs(session=self.session,
                               team_id=self.uid,
                               resource_type=ResourceTypeEnum.TABLE_DEFINITION.value)


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
        Parameters
        ----------
        team: Team
            The Team Resource to be updated

        """
        url = self._get_path(team.uid)
        updated = self.session.patch_resource(url, team.dump(), version=self._api_version)
        data = updated[self._individual_key]
        return self.build(data)

    def register(self, name: str, *, description: str = "") -> Team:
        """
        Create and upload new team.

        Automatically grants user READ, WRITE, and SHARE access to this team.

        Parameters
        ----------
        name: str
            Name of the team to be created.
        description: str
            Long-form description of the team to be created.

        """
        team = super().register(Team(name, description=description))
        user_id = UserCollection(self.session).me().uid
        team.update_user_action(user_id=user_id, actions=[READ, WRITE, SHARE])
        return team
