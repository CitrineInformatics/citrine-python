from os import environ
from typing import Optional

from citrine._session import Session
from citrine.resources.catalyst import CatalystResource
from citrine.resources.project import ProjectCollection
from citrine.resources.team import TeamCollection
from citrine.resources.user import UserCollection


class Citrine:
    """The entry point for interacting with the Citrine Platform.

    Create an instance of this class to access projects, teams,
    users, and other platform resources. All API calls are
    authenticated using the provided API key.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication. Obtain one from your
        platform's account settings page. Falls back to the
        ``CITRINE_API_KEY`` environment variable if not provided.
    scheme : str, optional
        URL scheme. Default: ``'https'``.
    host : str, optional
        Platform hostname, e.g. ``'mysite.citrine-platform.com'``.
        Falls back to the ``CITRINE_API_HOST`` environment
        variable if not provided.
    port : str, optional
        Network port. Default: ``None`` (use scheme default).

    Raises
    ------
    ValueError
        If ``host`` is not provided and ``CITRINE_API_HOST``
        is not set.

    Examples
    --------
    >>> from citrine import Citrine
    >>> client = Citrine(
    ...     api_key='your-api-key',
    ...     host='mysite.citrine-platform.com'
    ... )
    >>> for project in client.projects.list():
    ...     print(project.name)

    """

    def __init__(self,
                 api_key: str = None,
                 *,
                 scheme: str = None,
                 host: str = None,
                 port: Optional[str] = None):
        if api_key is None:
            api_key = environ.get('CITRINE_API_KEY')
        if scheme is None:
            scheme = 'https'

        if host is None:
            host = environ.get('CITRINE_API_HOST')
            if host is None:
                raise ValueError("No host passed and environmental "
                                 "variable CITRINE_API_HOST not set.")

        self.session: Session = Session(refresh_token=api_key,
                                        scheme=scheme,
                                        host=host,
                                        port=port
                                        )

    @property
    def projects(self) -> ProjectCollection:
        """Access all projects visible to the authenticated user.

        Returns
        -------
        ProjectCollection
            A collection supporting ``.list()``, ``.get(uid)``,
            and ``.register()`` operations on projects.

        """
        return ProjectCollection(self.session)

    @property
    def users(self) -> UserCollection:
        """Access all users on the platform.

        Returns
        -------
        UserCollection
            A collection supporting ``.list()`` and ``.get(uid)``
            operations on users.

        """
        return UserCollection(self.session)

    @property
    def teams(self) -> TeamCollection:
        """Access all teams visible to the authenticated user.

        Returns
        -------
        TeamCollection
            A collection supporting ``.list()``, ``.get(uid)``,
            and ``.register()`` operations on teams.

        """
        return TeamCollection(self.session)

    @property
    def catalyst(self) -> CatalystResource:
        """Access the Catalyst multi-tenant data platform.

        Returns
        -------
        CatalystResource
            A resource for interacting with Catalyst services.

        """
        return CatalystResource(self.session)
