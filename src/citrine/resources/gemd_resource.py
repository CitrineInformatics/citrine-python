"""Collection class for generic GEMD objects and templates."""
from typing import Type, Union, Optional, List, Tuple
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.api_error import ApiError
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.delete import _async_gemd_batch_delete
from citrine._session import Session


class GEMDResourceCollection(DataConceptsCollection[DataConcepts]):
    """A collection of any kind of GEMD objects/templates."""

    _path_template = 'projects/{project_id}/storables'
    _dataset_agnostic_path_template = 'projects/{project_id}/storables'

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    @classmethod
    def get_type(cls) -> Type[DataConcepts]:
        """Return the resource type in the collection."""
        return DataConcepts

    def _collection_for(self, model):
        collection = DataConcepts.get_collection_type(model)
        return collection(self.project_id, self.dataset_id, self.session)

    def build(self, data: dict) -> DataConcepts:
        """
        Build an arbitary GEMD object from a serialized dictionary.

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
        return super().build(data)

    def update(self, model: DataConcepts) -> DataConcepts:
        """Update a data model object using the appropriate collection."""
        return self._collection_for(model).update(model)

    def delete(self, uid: Union[UUID, str, LinkByUID, DataConcepts], *, dry_run=False):
        """
        Delete a GEMD resource from the appropriate collection.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, DataConcepts]
            A representation of the resource to delete (Citrine id, LinkByUID, or the object)
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        """
        model = self.get(uid)  # Get full object for collection lookup
        return self._collection_for(model).delete(model, dry_run=dry_run)

    def register(self, model: DataConcepts, *, dry_run=False) -> DataConcepts:
        """Register a GEMD object to the appropriate collection."""
        return self._collection_for(model).register(model, dry_run=dry_run)

    def register_all(self,
                     models: List[DataConcepts],
                     *,
                     dry_run=False,
                     status_bar=False) -> List[DataConcepts]:
        """
        Register multiple GEMD objects to each of their appropriate collections.

        Does so in an order that is guaranteed to store all linked items before the item that
        references them.

        If the GEMD objects have no UIDs, Citrine IDs will be assigned to them prior to passing
        them on to the server.  This is required as otherwise there is no way to determine how
        objects are related to each other.  When the registered objects are returned from the
        server, the input GEMD objects will be updated with whichever uids & _citr_auto:: tags are
        on the returned objects.  This means GEMD objects that already exist on the server will
        be updated with all their on-platform uids and tags.

        Parameters
        ----------
        models: List[DataConcepts]
            The data model objects to register. Can be different types.

        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        status_bar: bool
            Whether to display a status bar using the tqdm module to track progress in
            registration. Requires installing the optional tqdm module. Default: false

        Returns
        -------
        List[DataConcepts]
            The registered versions

        """
        # Endpoints are polymorphic now, so it doesn't matter which we hit
        collection = self._collection_for(list(models)[0])
        return collection.register_all(models, dry_run=dry_run, status_bar=status_bar)

    def async_update(self, model: DataConcepts, *,
                     dry_run: bool = False,
                     wait_for_response: bool = True,
                     timeout: float = 2 * 60,
                     polling_delay: float = 1.0,
                     return_model: bool = False) -> Optional[Union[UUID, DataConcepts]]:
        """
        [ALPHA] Update a particular element of the collection with data validation.

        Update a particular element of the collection, doing a deeper check to ensure that
        the dependent data objects are still with the (potentially) changed constraints
        of this change. This will allow you to make bounds and allowed named/labels changes
        to templates.

        Parameters
        ----------
        model: DataConcepts
            The DataConcepts object.
        dry_run: bool
            Whether to actually update the item or run a dry run of the update operation.
            Dry run is intended to be used for validation. Default: false
        wait_for_response: bool
            Whether to poll for the eventual response. This changes the return type (see
            below).
        timeout: float
            How long to poll for the result before giving up. This is expressed in
            (fractional) seconds.
        polling_delay: float
            How long to delay between each polling retry attempt.
        return_model: bool
            Whether or not to return an updated version of the resource
            If wait_for_response is False, then this argument has no effect

        Returns
        -------
        Optional[UUID]
            If wait_for_response if True, then this call will poll the backend, waiting
            for the eventual job result. In the case of successful validation/update,
            a return value of None is provided unless return_model is True, in which case
            the updated resource is fetched and returned. In the case of a failure
            validating or processing the update, an exception (JobFailureError) is raised
            and an error message is logged with the underlying reason of the failure.

            If wait_for_response if False, A job ID (of type UUID) is returned that one
            can use to poll for the job completion and result with the
            :func:`~citrine.resources.DataConceptsCollection.poll_async_update_job`
            method.

        """
        return self._collection_for(model).async_update(
            model,
            dry_run=dry_run,
            wait_for_response=wait_for_response,
            timeout=timeout,
            polling_delay=polling_delay,
            return_model=return_model
        )

    def batch_delete(
            self,
            id_list: List[Union[LinkByUID, UUID, str, BaseEntity]],
            *,
            timeout: float = 2 * 60,
            polling_delay: float = 1.0
    ) -> List[Tuple[LinkByUID, ApiError]]:
        """
        Remove a set of GEMD objects.

        You may provide GEMD objects that reference each other, and the objects
        will be removed in the appropriate order.

        A failure will be returned if the object cannot be deleted due to an external
        reference.

        All data objects must be associated with this dataset resource. You must also
        have write access on this dataset.

        If you wish to delete more than 50 objects, queuing of deletes requires that
        the types of objects be known, and thus you _must_ provide ids in the form
        of BaseEntities.

        Also note that Attribute Templates cannot be deleted at present.

        Parameters
        ----------
        id_list: List[Union[LinkByUID, UUID, str, BaseEntity]]
            A list of the IDs of data objects to be removed. They can be passed
            as a LinkByUID tuple, a UUID, a string, or the object itself. A UUID
            or string is assumed to be a Citrine ID, whereas a LinkByUID or
            BaseEntity can also be used to provide an external ID.

        Returns
        -------
        List[Tuple[LinkByUID, ApiError]]
            A list of (LinkByUID, api_error) for each failure to delete an object.
            Note that this method doesn't raise an exception if an object fails to be
            deleted.

        """
        return _async_gemd_batch_delete(id_list, self.project_id, self.session, self.dataset_id,
                                        timeout=timeout, polling_delay=polling_delay)
