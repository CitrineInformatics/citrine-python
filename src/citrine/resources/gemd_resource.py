"""Collection class for generic GEMD objects and templates."""
from typing import Type, Union, Optional, List, Iterator
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine._session import Session


class GEMDEntityCollection(DataConceptsCollection[DataConcepts]):
    """A collection of any kind of GEMD objects/templates."""

    _path_template = 'projects/{project_id}/storables'
    _dataset_agnostic_path_template = 'projects/{project_id}/storables'
    _individual_key = None
    _collection_key = None
    _resource = DataConcepts

    def __init__(self, project_id: UUID, dataset: 'Dataset', session: Session):
        # Forward reference of 'Dataset' to avoid cyclic import
        self.project_id = project_id
        self.session = session

        self.dataset = dataset
        self.dataset_id = self.dataset.uid if self.dataset is not None else None

    @classmethod
    def get_type(cls) -> Type[DataConcepts]:
        """Return the resource type in the collection."""
        return DataConcepts

    def build(self, data: dict) -> DataConcepts:
        """
        Build an arbitary GEMD entity from a serialized dictionary.

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
        """Update a GEMD entity using the appropriate collection."""
        if self.dataset is None:
            raise RuntimeError("Must specify a dataset in order to update a GEMD entity.")
        return self.dataset.update(model)

    def delete(self, uid: Union[UUID, str, LinkByUID, DataConcepts], *,
               dry_run=False):
        """
        Delete a GEMD entity from the appropriate collection.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, DataConcepts]
            A representation of the resource to delete (Citrine id, LinkByUID, or the object)
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        """
        if self.dataset is None:
            raise RuntimeError("Must specify a dataset in order to delete a GEMD entity.")
        return self.dataset.delete(uid, dry_run=dry_run)

    def register(self, model: DataConcepts, *, dry_run=False) -> DataConcepts:
        """Register a GEMD entity to the appropriate collection."""
        if self.dataset is None:
            raise RuntimeError("Must specify a dataset in order to register a GEMD entity.")
        return self.dataset.register(model, dry_run=dry_run)

    def register_all(self, models: List[DataConcepts], *,
                     dry_run=False) -> List[DataConcepts]:
        """
        Register multiple GEMD entities to each of their appropriate collections.

        Does so in an order that is guaranteed to store all linked items before the item that
        references them.

        The uids of the input data concepts resources are updated with their on-platform uids.
        This supports storing an object that has a reference to an object that doesn't have a uid.

        Parameters
        ----------
        models: List[DataConcepts]
            The resources to register. Can be different types.

        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        Returns
        -------
        List[DataConcepts]
            The registered versions

        """
        if self.dataset is None:
            raise RuntimeError("Must specify a dataset in order to register GEMD entities.")
        return self.dataset.register_all(models, dry_run=dry_run)

    def async_update(self, model: DataConcepts, *,
                     dry_run: bool = False,
                     wait_for_response: bool = True,
                     timeout: float = 2 * 60,
                     polling_delay: float = 1.0,
                     return_model: bool = False) -> Optional[Union[UUID, DataConcepts]]:
        """Asynchronous updating is only available on specific collections of GEMD entities."""
        raise NotImplementedError("Asynchronous updating is only available"
                                  " on a specific collection of GEMD entities.")
