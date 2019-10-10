"""Resources that represent both collections of processors."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.processors import Processor

CreationType = TypeVar('CreationType', bound=Processor)


class ProcessorCollection(Collection[Processor]):
    """Represents the collection of all projects as well as the resources belonging to it."""

    _path_template = '/projects/{project_id}/modules'
    _collection_key = 'entry'
    _individual_key = None

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Processor:
        """Build an individual Processor."""
        processor = Processor.build(data)
        processor.session = self.session
        return processor
