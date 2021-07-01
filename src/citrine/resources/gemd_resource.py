"""Collection class for generic GEMD objects and templates."""
from typing import Type, Union, Optional, List, Iterator
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine._session import Session


class GEMDResourceCollection(DataConceptsCollection[DataConcepts]):
    """A collection of any kind of GEMD objects/templates."""

    _path_template = 'projects/{project_id}/storables'
    _dataset_agnostic_path_template = 'projects/{project_id}/storables'
    _individual_key = None
    _collection_key = None
    _resource = DataConcepts

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    @classmethod
    def get_type(cls) -> Type[DataConcepts]:
        """Return the resource type in the collection."""
        return DataConcepts

    def build(self, data: dict) -> DataConcepts:
        """
        Build an arbitary GEMD resource from a serialized dictionary.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A serialized data model object.

        Returns
        -------
        DataConcepts
            A data model object built from the dictionary.

        """
        return DataConcepts.build(data)

    def update(self, model: DataConcepts) -> DataConcepts:
        """To update an arbitrary GEMD resource, please use dataset.update instead."""
        raise NotImplementedError("To update an arbitary GEMD resource,"
                                  " please use dataset.update instead.")

    def delete(self, model: DataConcepts) -> DataConcepts:
        """To delete an arbitrary GEMD resource, please use dataset.delete instead."""
        raise NotImplementedError("To delete an arbitary GEMD resource,"
                                  " please use dataset.delete instead.")

    def register(self, model: DataConcepts, *, dry_run=False):
        """To register an arbitrary GEMD resource, please use dataset.register instead."""
        raise NotImplementedError("To register an arbitary GEMD resource,"
                                  " please use dataset.register instead.")

    def register_all(self, models: List[DataConcepts], *,
                     dry_run=False) -> List[DataConcepts]:
        """To register a list of GEMD resources, please use dataset.register_all instead."""
        raise NotImplementedError("To register a list of GEMD resources,"
                                  " please use dataset.register_all instead.")

    def async_update(self, model: DataConcepts, *,
                     dry_run: bool = False,
                     wait_for_response: bool = True,
                     timeout: float = 2 * 60,
                     polling_delay: float = 1.0,
                     return_model: bool = False) -> Optional[Union[UUID, DataConcepts]]:
        """Asynchronous updates are only available through specific GEMD resource collections."""
        raise NotImplementedError("Asynchronous updates are only available"
                                  " through specific GEMD resource collections.")

    def poll_async_update_job(self, job_id: UUID, *, timeout: float = 2 * 60,
                              polling_delay: float = 1.0) -> None:
        """Asynchronous polling is only available through specific GEMD resource collections."""
        raise NotImplementedError("Asynchronous polling is only available"
                                  " through specific GEMD resource collections.")

    def _get_relation(self, relation: str, uid: Union[UUID, str, LinkByUID, BaseEntity],
                      scope: Optional[str] = None, forward: bool = True, per_page: int = 100
                      ) -> Iterator[DataConcepts]:
        """Relationship searching is only available through specific GEMD resource collections."""
        raise NotImplementedError("Relationship searching is only available"
                                  " through specific GEMD resource collections.")
