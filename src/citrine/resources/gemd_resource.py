"""Collection class for generic GEMD objects and templates."""
from collections import defaultdict
from typing import Type, Union, Optional, List
from uuid import UUID

from gemd.util import writable_sort_order
from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object import MeasurementSpec, MeasurementRun, MaterialSpec, MaterialRun, \
    ProcessSpec, ProcessRun, IngredientSpec, IngredientRun
from gemd.entity.template import PropertyTemplate, MaterialTemplate, MeasurementTemplate, \
    ParameterTemplate, ProcessTemplate, ConditionTemplate

from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.ingredient_run import IngredientRunCollection
from citrine.resources.ingredient_spec import IngredientSpecCollection
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.material_template import MaterialTemplateCollection
from citrine.resources.measurement_run import MeasurementRunCollection
from citrine.resources.measurement_spec import MeasurementSpecCollection
from citrine.resources.measurement_template import MeasurementTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.process_run import ProcessRunCollection
from citrine.resources.process_spec import ProcessSpecCollection
from citrine.resources.process_template import ProcessTemplateCollection
from citrine.resources.property_template import PropertyTemplateCollection
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

    def _collection_for(self, model):
        if isinstance(model, MeasurementTemplate):
            return MeasurementTemplateCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, MeasurementSpec):
            return MeasurementSpecCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, MeasurementRun):
            return MeasurementRunCollection(self.project_id, self.dataset_id, self.session)

        if isinstance(model, MaterialTemplate):
            return MaterialTemplateCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, MaterialSpec):
            return MaterialSpecCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, MaterialRun):
            return MaterialRunCollection(self.project_id, self.dataset_id, self.session)

        if isinstance(model, ProcessTemplate):
            return ProcessTemplateCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, ProcessSpec):
            return ProcessSpecCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, ProcessRun):
            return ProcessRunCollection(self.project_id, self.dataset_id, self.session)

        if isinstance(model, IngredientSpec):
            return IngredientSpecCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, IngredientRun):
            return IngredientRunCollection(self.project_id, self.dataset_id, self.session)

        if isinstance(model, PropertyTemplate):
            return PropertyTemplateCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, ParameterTemplate):
            return ParameterTemplateCollection(self.project_id, self.dataset_id, self.session)
        if isinstance(model, ConditionTemplate):
            return ConditionTemplateCollection(self.project_id, self.dataset_id, self.session)

    def _resolve_model(self, uid: Union[UUID, str, LinkByUID, DataConcepts]) -> DataConcepts:
        if isinstance(uid, (UUID, str, LinkByUID)):
            return self.get(uid)
        else:
            return uid

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
        """Update a GEMD resource using the appropriate collection."""
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
        model = self._resolve_model(uid)
        return self._collection_for(model).delete(model, dry_run=dry_run)

    def register(self, model: DataConcepts, *, dry_run=False) -> DataConcepts:
        """Register a GEMD resource to the appropriate collection."""
        return self._collection_for(model).register(model, dry_run=dry_run)

    def register_all(self, models: List[DataConcepts], *, dry_run=False) -> List[DataConcepts]:
        """
        Register multiple GEMD resources to each of their appropriate collections.

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
        resources = list()
        by_type = defaultdict(list)
        for obj in models:
            by_type[obj.typ].append(obj)
        typ_groups = sorted(list(by_type.values()), key=lambda x: writable_sort_order(x[0]))
        batch_size = 50
        for typ_group in typ_groups:
            num_batches = len(typ_group) // batch_size
            for batch_num in range(num_batches + 1):
                batch = typ_group[batch_num * batch_size: (batch_num + 1) * batch_size]
                if batch:  # final batch is empty when batch_size divides len(typ_group)
                    registered = self._collection_for(batch[0]) \
                        .register_all(batch, dry_run=dry_run)
                    for prewrite, postwrite in zip(batch, registered):
                        if isinstance(postwrite, BaseEntity):
                            prewrite.uids = postwrite.uids
                    resources.extend(registered)
        return resources

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
