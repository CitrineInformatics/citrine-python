"""Resources that represent collections of modules."""
from uuid import UUID
from typing import TypeVar, Union

from citrine._rest.collection import Collection
from citrine._session import Session
from citrine.exceptions import CitrineException
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

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> Module:
        """Build an individual module."""
        module = Module.build(data)
        module.session = self.session
        return module


ModuleType = TypeVar('ModuleType', bound='Module')


class AbstractModuleCollection(Collection[ModuleType]):
    """Abstract class for representing collection of modules."""

    _module_type = None

    def delete(self, uid: Union[UUID, str]):
        """Modules cannot be deleted at this time."""
        msg = "Modules cannot be deleted at this time. Use 'archive' instead."
        raise NotImplementedError(msg)

    def archive(self, module_id: Union[UUID, str]) -> ModuleType:
        """Archiving a module removes it from view, but is not a hard delete."""
        try:
            module = self.get(module_id)
        except CitrineException:
            raise RuntimeError(f"{self._module_type} with id {module_id} was not found, "
                               f"and hence cannot be archived.")
        module.archived = True
        return self.update(module)

    def restore(self, module_id: Union[UUID, str]) -> ModuleType:
        """Restore an archived module."""
        try:
            module = self.get(module_id)
        except CitrineException:
            raise RuntimeError(f"{self._module_type} with id {module_id} was not found, "
                               f"and hence cannot be restored.")
        module.archived = False
        return self.update(module)
