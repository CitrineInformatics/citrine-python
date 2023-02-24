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
        Default: environ.get('CITRINE_API_KEY')
    scheme: str
        Networking protocol; usually https.  Default: https
    host: str
        Host URL, generally '<your_site>.citrine-platform.com'.
        Default: environ.get('CITRINE_API_HOST')
    port: Optional[str]
        Optional networking port.  Default: None

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
        """Return a resource representing all visible projects."""
        return ProjectCollection(self.session)

    @property
    def users(self) -> UserCollection:
        """Return the collection of all users."""
        return UserCollection(self.session)

    @property
    def teams(self) -> TeamCollection:
        """Returns a resource representing all visible teams."""
        return TeamCollection(self.session)
