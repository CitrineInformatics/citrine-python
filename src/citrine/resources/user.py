"""Resources that represent both individual and collections of users."""
from typing import Optional

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session


class User(Resource['User']):
    """
    A Citrine User.

    Parameters
    ----------
    screen_name: str
        Screen name of the user.
    email: str
        Email address of the user.
    position: str
        Position of the user.
    is_admin: bool
        Whether or not the user is an administrator.
    session: Session, optional
        Citrine session used to connect to the database.

    """

    uid = properties.Optional(properties.UUID, 'id')
    screen_name = properties.String('screen_name')
    position = properties.String('position')
    email = properties.String('email')
    is_admin = properties.Boolean('is_admin')

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
        return '<User {!r}>'.format(self.screen_name)

    def get(self):
        """Retrieve a specific user from the database."""
        raise NotImplementedError("Get Not Implemented in Citrine Platform")


class UserCollection(Collection[User]):
    """Represents the collection of all users."""

    _path_template = '/users'
    _collection_key = 'users'
    _individual_key = 'user'
    _resource = User

    def __init__(self, session: Session):
        self.session: Session = session

    def me(self):
        """Get information about the current user."""
        data = self.session.get_resource('{}/me'.format(self._path_template))
        return self.build(data)

    def build(self, data):
        """
        Build an individual user from a dictionary.

        Parameters
        ----------
        data: dict
          A dictionary representing the user.

        Returns
        -------
        User
          The user created from data.

        """
        user = User.build(data)
        user.session = self.session
        return user

    def register(self,
                 screen_name: str,
                 email: str,
                 position: str,
                 is_admin: bool) -> User:
        """Register a User."""
        return super().register(User(
            screen_name=screen_name,
            email=email,
            position=position,
            is_admin=is_admin))
