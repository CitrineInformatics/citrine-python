"""Resources that represent collections of processors."""
from uuid import UUID
from typing import TypeVar, Union

from citrine._session import Session
from citrine.exceptions import CitrineException
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
        processor = Processor.build(data)
        processor.session = self.session
        return processor

    def delete(self, uid: Union[UUID, str]):
        """Modules cannot be deleted at this time."""
        msg = "Processors cannot be deleted at this time. Use 'archive' instead."
        raise NotImplementedError(msg)

    def archive(self, module_id: Union[UUID, str]) -> Processor:
        """Archiving a processor removes it from view, but is not a hard delete."""
        try:
            module = self.get(module_id)
        except CitrineException:
            msg = f"Processor with id {module_id} was not found, and hence cannot be archived."
            raise RuntimeError(msg)
        module.archived = True
        return self.update(module)
