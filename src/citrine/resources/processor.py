"""Resources that represent collections of processors."""
from uuid import UUID
from typing import TypeVar

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.informatics.processors import Processor

CreationType = TypeVar('CreationType', bound=Processor)


class ProcessorCollection(Collection[Processor]):
    """[ALPHA] Represents the collection of all processors for a project.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _path_template = '/projects/{project_id}/modules'
    _individual_key = None
    _resource = Processor
    _module_type = 'PROCESSOR'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Processor:
        """Build an individual Processor."""
        processor = Processor.build(data)
        processor.session = self.session
        return processor
