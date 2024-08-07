"""Collection class for generic GEMD objects and templates."""
import re
from typing import Type, Union, List, Tuple, Iterable, Optional
from uuid import UUID, uuid4

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID
from gemd.util import recursive_flatmap, recursive_foreach, set_uuids, \
    make_index, substitute_objects
from tqdm.auto import tqdm

from citrine.resources.api_error import ApiError
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection, \
    CITRINE_SCOPE, CITRINE_TAG_PREFIX
from citrine.resources.delete import _async_gemd_batch_delete
from citrine._session import Session
from citrine._utils.batcher import Batcher
from citrine._utils.functions import _pad_positional_args, replace_objects_with_links, scrub_none


BATCH_SIZE = 50


class GEMDResourceCollection(DataConceptsCollection[DataConcepts]):
    """A collection of any kind of GEMD objects/templates."""

    _collection_key = 'storables'

    def __init__(
        self,
        *args,
        dataset_id: UUID = None,
        session: Session = None,
        team_id: UUID = None,
        project_id: Optional[UUID] = None
    ):
        super().__init__(*args,
                         team_id=team_id,
                         dataset_id=dataset_id,
                         session=session,
                         project_id=project_id)
        args = _pad_positional_args(args, 3)
        self.project_id = project_id or args[0]
        self.dataset_id = dataset_id or args[1]
        self.session = session or args[2]
        self.team_id = team_id

    @classmethod
    def get_type(cls) -> Type[DataConcepts]:
        """Return the resource type in the collection."""
        return DataConcepts

    def _collection_for(self, model):
        collection = DataConcepts.get_collection_type(model)
        return collection(team_id=self.team_id, dataset_id=self.dataset_id, session=self.session)

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

    def register_all(self,
                     models: Iterable[DataConcepts],
                     *,
                     dry_run=False,
                     status_bar=False,
                     include_nested=False) -> List[DataConcepts]:
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

        This method has the same behavior as `register`, except that no models will be
        written if any one of them is invalid.  Using this method should yield significant
        improvements to write speed over separate calls to `register`.

        Parameters
        ----------
        models: Iterable[DataConcepts]
            The data model objects to register. Can be different types.

        dry_run: bool
            Whether to actually register the item or run a dry run of the register operation.
            Dry run is intended to be used for validation. Default: false

        status_bar: bool
            Whether to display a status bar using the tqdm module to track progress in
            registration. Requires installing the optional tqdm module. Default: false

        include_nested: bool
            Whether to just register the objects passed in the list, or include nested objects
            (e.g., obj.process, obj.spec.template, ...).  Default: false

        Returns
        -------
        List[DataConcepts]
            The registered versions

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to register a data model object.")
        path = self._get_path()
        params = {'dry_run': dry_run}

        if include_nested:
            models = recursive_flatmap(models, lambda o: [o], unidirectional=False)

        temp_scope = str(uuid4())
        scope = temp_scope if dry_run else CITRINE_SCOPE
        set_uuids(models, scope=scope)

        resources = list()
        result_index = dict()
        if dry_run:
            batcher = Batcher.by_dependency()
        else:
            batcher = Batcher.by_type()

        if status_bar:
            desc = "Verifying GEMDs" if dry_run else "Registering GEMDs"
            iterator = tqdm(batcher.batch(models, BATCH_SIZE), leave=False, desc=desc)
        else:
            iterator = batcher.batch(models, BATCH_SIZE)

        for batch in iterator:
            objects = [replace_objects_with_links(scrub_none(model.dump())) for model in batch]
            response_data = self.session.put_resource(
                path + '/batch',
                json={'objects': objects},
                params=params
            )
            registered = [self.build(obj) for obj in response_data['objects']]
            result_index.update(make_index(registered))
            substitute_objects(registered, result_index, inplace=True)

            if not dry_run:
                # Platform may add a CITRINE_SCOPE uid and citr_auto tags; update locals
                for obj in batch:
                    result = result_index[obj.to_link()]
                    obj.uids.update({k: v for k, v in result.uids.items()})
                    if result.tags is not None:
                        obj.tags = list(result.tags)
            else:
                # Remove of the tags/uids the platform spuriously added
                # this might leave objects with just the temp ids, which we want to strip later
                for obj in batch:
                    result = result_index[obj.to_link()]
                    if CITRINE_SCOPE not in obj.uids:
                        citr_id = result.uids.pop(CITRINE_SCOPE, None)
                        result_index.pop(LinkByUID(scope=CITRINE_SCOPE, id=citr_id), None)
                    if result.tags is not None:
                        todo = [tag for tag in result.tags
                                if re.match(f"^{CITRINE_TAG_PREFIX}::", tag)]
                        for tag in todo:  # Covering this block would require dark art
                            if tag not in obj.tags:
                                result.tags.remove(tag)

            resources.extend(registered)

        if dry_run:  # No-op if not dry-run
            recursive_foreach(list(models) + list(resources),
                              lambda x: x.uids.pop(temp_scope, None))  # Strip temp uids
        return resources

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
        return _async_gemd_batch_delete(
            id_list=id_list,
            team_id=self.team_id,
            session=self.session,
            dataset_id=self.dataset_id,
            timeout=timeout,
            polling_delay=polling_delay)
