"""Resources that represent both individual and collections of teams."""
from typing import Optional, Union, Iterable, Tuple, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.resources.response import Response


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
    status: str
        Status of the team.
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
        raise NotImplementedError("Can't make teams yet")

    def list(self, *,
             page: Optional[int] = None,
             per_page: int = 1000) -> Iterator[Team]:
        """
        List teams using pagination.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 1000.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterator[Team]
            Teams in this collection.

        """
        return super().list(page=page, per_page=per_page)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """
        [ALPHA] Delete a particular team.

        If the team is not empty, then the team's resources will be deleted
        """
        return super().delete(uid)  # pragma: no cover

    def update(self, model: Team) -> Team:
        """Teams can be updated."""
        # Todo we can edit teams now
        pass

    def _fetch_page_search(self, page: Optional[int] = None,
                           per_page: Optional[int] = None,
                           search_params: Optional[dict] = None) -> Tuple[Iterable[dict], str]:
        """
        Fetch resources that match the supplied search parameters.

        Fetches resources that match the supplied ``search_params``, by calling ``_fetch_page``
        with ``checked_post``, the path to the POST resource-type/search endpoint, any pagination
        parameters, and the request body to the search endpoint.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return. Default is 20.
        search_params: dict, optional
            A ``dict`` representing a request body that could be sent to a POST request. The "json"
            field should be passed as the key for the outermost ``dict``, with its value the
            request body, so that we can easily unpack the keyword argument when it gets passed to
            ``fetch_func``, e.g., ``{'name': {'value': 'Team', 'search_method': 'SUBSTRING'} }``

        Returns
        -------
        Iterable[dict]
            Elements in this collection.
        str
            The next uri if one is available, empty string otherwise

        """
        # Making 'json' the key of the outermost dict, so that search_params can be passed
        # directly to the function making the request with keyword expansion
        json_body = {} if search_params is None else {'json': {'search_params': search_params}}

        path = self._get_path() + "/search"

        return self._fetch_page(path=path, fetch_func=self.session.post_resource,
                                page=page, per_page=per_page,
                                json_body=json_body)
