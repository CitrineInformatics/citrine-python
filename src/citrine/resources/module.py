"""Resources that represent collections of design spaces."""
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.modules import Module


class ModuleCollection(Collection[Module]):
    """Represents the collection of all modules as well as the resources belonging to it.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _path_template = '/projects/{project_id}/modules'
    _individual_key = None
    _resource = Module

    def __init__(self, project_id: UUID, session: Session = Session()):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Module:
        """Build an individual module."""
        module = Module.build(data)
        module.session = self.session
        return module
