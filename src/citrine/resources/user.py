"""Resources that represent both individual and collections of projects."""
from typing import Optional

from citrine._serialization import properties
from citrine._session import Session
from citrine._serialization.serializable import Serializable


class User(Serializable['User']):
    """A Citrine User."""

    uid = properties.Optional(properties.UUID, 'id')
    screen_name = properties.String('screenName')
    position = properties.String('position')
    email = properties.String('email')
    is_admin = properties.Boolean('isAdmin')

    def __init__(self,
                 screen_name: str,
                 email: str,
                 position: str,
                 is_admin: bool,
                 session: Optional[Session] = None):
        self.email: str = email
        self.position: str = position
        self.screen_name: str = screen_name
        self.is_admin: bool = is_admin
        self.session: Optional[Session] = session

    def __str__(self):
        return '<User {}>'.format(self.screen_name)


class UserCollection:
    """Represents the collection of all projects as well as the resources belonging to it."""

    __path_template__ = '/users'
    _response_key = 'users'
    _resource = User

    def __init__(self, session: Session):
        self.session: Session = session
