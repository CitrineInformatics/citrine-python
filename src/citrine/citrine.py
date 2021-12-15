from warnings import warn
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
                 legacy_scheme: Optional[str] = None,
                 host: str = environ.get('CITRINE_API_HOST'),
                 port: Optional[str] = None,
                 *,
                 scheme: str = 'https'):
        if legacy_scheme is not None:
            warn("Creating a session with positional arguments other than refresh_token "
                 "is deprecated; use keyword arguments to specify scheme, host and port.",
                 DeprecationWarning)
            if scheme != 'https':
                raise ValueError("Specify legacy_scheme or scheme, not both.")
            scheme = legacy_scheme

        self.session: Session = Session(refresh_token=api_key,
                                        scheme=scheme,
                                        host=host,
                                        port=port
                                        )

    @property
    def projects(self) -> ProjectCollection:
        """Return a resource representing all visible projects."""
        # Fetch the version of accounts

        if self.session._accounts_service_v3:
            warn("Your Citrine Platform deployment has migrated to the CP2 release of the"
                 " Citrine Platform Web Interface. See our FAQ for details.", UserWarning)
        return ProjectCollection(self.session)

    @property
    def users(self) -> UserCollection:
        """Return the collection of all users."""
        return UserCollection(self.session)

    @property
    def teams(self) -> TeamCollection:
        """Returns a resource representing all visible teams."""
        # Fetch the version of accounts
        if self.session._accounts_service_v3:
            return TeamCollection(self.session)
        else:
            raise NotImplementedError("This method is inoperable until your Citrine Platform "
                                      "deployment has migrated to the CP2 release of the Citrine "
                                      "Platform Web Interface. See our FAQ for details.")
