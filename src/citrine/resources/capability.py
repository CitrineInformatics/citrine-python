"""Resources that represent both collections of capabilities."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.capabilities import Capability

CreationType = TypeVar('CreationType', bound=Capability)


class CapabilityCollection(Collection[Capability]):
    """Represents the collection of all capabilities as well as the resources belonging to it."""

    _path_template = '/projects/{project_id}/modules'
    _collection_key = 'entries'
    _individual_key = None
    _resource = Capability

    def __init__(self, project_id: UUID, session: Session = Session()):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Capability:
        """Build an individual Capability."""
        capability = Capability.build(data)
        capability.session = self.session
        return capability

    def register(self, model: CreationType) -> CreationType:
        """Registers a capability."""
        return super().register(model)
