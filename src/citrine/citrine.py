from typing import Optional
from citrine._session import Session
from citrine.resources.project import ProjectCollection
from citrine.resources.user import UserCollection


DEFAULT_HOST: str = 'citrine.io'
DEFAULT_SCHEME: str = 'https'


class Citrine:
    """The entry point for interacting with the Citrine Platform."""

    def __init__(self,
                 api_key: str,
                 scheme: str = DEFAULT_SCHEME,
                 host: str = DEFAULT_HOST,
                 port: Optional[str] = None):
        self.session: Session = Session(api_key, scheme, host, port)

    @property
    def projects(self) -> ProjectCollection:
        """Return a resource representing all visible projects."""
        return ProjectCollection(self.session)

    @property
    def users(self) -> UserCollection:
        """Return the collection of all users."""
        return UserCollection(self.session)
