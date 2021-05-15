"""Resources that represent collections of processors."""
from uuid import UUID
from typing import TypeVar

from citrine._session import Session
from citrine.resources.module import AbstractModuleCollection
from citrine.informatics.processors import Processor

CreationType = TypeVar('CreationType', bound=Processor)


class ProcessorCollection(AbstractModuleCollection[Processor]):
    """Represents the collection of all processors for a project.

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
        processor: Processor = Processor.build(data)
        processor._session = self.session
        processor._project_id = self.project_id
        return processor
