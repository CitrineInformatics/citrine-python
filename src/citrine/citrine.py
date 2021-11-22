from os import environ
from typing import Optional

from citrine._session import Session
from citrine.resources.project import ProjectCollection
from citrine.resources.team import TeamCollection
from citrine.resources.user import UserCollection


class Citrine:
    """The entry point for interacting with the Citrine Platform.

    Parameters
    ----------
    api_key: str
        Unique key that allows a user to access the Citrine Platform.
    scheme: str
        Networking protocol; usually https
    host: str
        Host URL, generally '<your_site>.citrine-platform.com'
    port: Optional[str]
        Optional networking port

    """

    def __init__(self,
                 api_key: str = environ.get('CITRINE_API_KEY'),
                 scheme: str = 'https',
                 host: str = environ.get('CITRINE_API_HOST'),
                 port: Optional[str] = None):
        self.session: Session = Session(api_key, scheme, host, port)

    @property
    def projects(self) -> ProjectCollection:
        """Return a resource representing all visible projects."""
        if self.session._accounts_service_v3:
            UserWarning("You might want to use citrine.teams to find a team specific project")
        return ProjectCollection(self.session)

    @property
    def users(self) -> UserCollection:
        """Return the collection of all users."""
        return UserCollection(self.session)

    @property
    def teams(self) -> TeamCollection:
        """Returns a resource representing all visible teams."""
        if self.session._accounts_service_v3:
            return TeamCollection(self.session)
        else:
            raise NotImplementedError("Teams are not available, please continue using projects")
