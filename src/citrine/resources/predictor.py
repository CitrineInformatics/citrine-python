"""Resources that represent collections of predictors."""
from functools import partial
from typing import Iterable, TypeVar, Optional, Union
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument, format_escaped_url
from citrine.exceptions import Conflict
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors import Predictor
from citrine.resources.module import AbstractModuleCollection

from deprecation import deprecated

CreationType = TypeVar('CreationType', bound=Predictor)


class AutoConfigureMode(BaseEnumeration):
    """[ALPHA] The format to use in building auto-configured assets.

    * PLAIN corresponds to a single-row GEM table and plain predictor
    * FORMULATION corresponds to a multi-row GEM table and formulations predictor
    * INFER auto-detects the GEM table and predictor type
    """

    PLAIN = 'PLAIN'
    FORMULATION = 'FORMULATION'
    INFER = 'INFER'


class PredictorCollection(AbstractModuleCollection[Predictor]):
    """Represents the collection of all predictors for a project.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _api_version = 'v3'
    _path_template = '/projects/{project_id}/predictors'
    _individual_key = None
    _resource = Predictor
    _collection_key = 'response'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def _predictors_path(self, subpath: str, uid: Union[UUID, str] = None) -> str:
        path_template = self._path_template + (f"/{uid}" if uid else "") + f"/{subpath}"
        return format_escaped_url(path_template, project_id=self.project_id)

    # TODO: Until we expose predictor versions in the SDK, and thus expose the
    # difference between archving a predictor root and version, we should
    # report the root's archive status.
    def _inject_archive_info(self, predictor: Predictor, is_archived: bool = None) -> Predictor:
        # Allows specifying the root predictor archive status, or auto-detecting it.
        archived = self.root_is_archived(predictor.uid) if is_archived is None else is_archived
        if archived:
            predictor.archived_by = predictor.updated_by
            predictor.archive_time = predictor.update_time
        else:
            predictor.archived_by = None
            predictor.archive_time = None
        return predictor

    # TODO: Same as above
    def _build_collection_elements(self, collection: Iterable[dict], is_archived: bool = None) \
            -> Iterable[Predictor]:
        for pred in super()._build_collection_elements(collection):
            yield self._inject_archive_info(pred, is_archived)

    def _build_archived_collection(self, collection: Iterable[dict]) -> Iterable[Predictor]:
        return self._build_collection_elements(collection, True)

    def _build_unarchived_collection(self, collection: Iterable[dict]) -> Iterable[Predictor]:
        return self._build_collection_elements(collection, False)

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor: Predictor = Predictor.build(data)
        predictor._session = self.session
        predictor._project_id = self.project_id
        return predictor

    def get(self, uid: Union[UUID, str]) -> Predictor:
        """Get a particular element of the collection."""
        predictor = super().get(uid)
        return self._inject_archive_info(predictor)

    def register(self, predictor: Predictor) -> Predictor:
        """Register and train a Predictor."""
        created_predictor = super().register(predictor)

        # If the initial response is invalid, just return it.
        # If not, kick off training since we never exposed saving a model without it,
        # so we should continue to do it automatically.
        if created_predictor.failed():
            return created_predictor
        else:
            return self._train(created_predictor.uid)

    def update(self, predictor: Predictor) -> Predictor:
        """Update and train a Predictor."""
        updated_predictor = super().update(predictor)

        # The /api/v3/predictors endpoint switched (un)archive from a field on the update payload
        # to their own endpoints. To maintain backwards compatibility, all predictors have an
        # _archived field set by the archived property. It will be archived if True, and restored
        # if False. It defaults to None, which does nothing. The value is reset afterwards.
        if predictor._archived is True:
            self.archive_root(predictor.uid)
        elif predictor._archived is False:
            self.restore_root(predictor.uid)
        predictor._archived = None

        # If the initial response is invalid, just return it
        # If not, kick off training since we never exposed saving a model without training
        # so we should continue to do it automatically
        if updated_predictor.failed():
            return updated_predictor
        else:
            return self._train(updated_predictor.uid)

    def _train(self, uid: Union[UUID, str]) -> Predictor:
        path = self._predictors_path("train", uid)
        entity = self.session.put_resource(path, {}, version=self._api_version)
        predictor = self.build(entity)
        return self._inject_archive_info(predictor)

    def archive_root(self, uid: Union[UUID, str]):
        """Archive a root predictor.

        uid: Union[UUID, str]
            Unique identifier of the predictor to archive.

        """
        path = self._predictors_path("archive", uid)
        self.session.put_resource(path, {}, version=self._api_version)

    def restore_root(self, uid: Union[UUID, str]):
        """Restore an archived root predictor.

        uid: Union[UUID, str]
            Unique identifier of the predictor to restore.

        """
        path = self._predictors_path("restore", uid)
        self.session.put_resource(path, {}, version=self._api_version)

    def root_is_archived(self, uid: Union[UUID, str]) -> bool:
        """Determine if the predictor root is archived.

        uid: Union[UUID, str]
            Unique identifier of the predictor to check.
        """
        uid = str(uid)
        return any(uid == str(archived_pred.uid) for archived_pred in self.list_archived())

    @deprecated(deprecated_in="1.39.0", removed_in="2.0.0",
                details="archive() is deprecated in favor of archive_root().")
    def archive(self, uid: Union[UUID, str]) -> Predictor:
        """[DEPRECATED] Archive a root predictor."""
        self.archive_root(uid)
        return self.get(uid)

    @deprecated(deprecated_in="1.39.0", removed_in="2.0.0",
                details="restore() is deprecated in favor of restore_root().")
    def restore(self, uid: Union[UUID, str]) -> Predictor:
        """[DEPRECATED] Restore a root predictor."""
        self.restore_root(uid)
        return self.get(uid)

    def list(self, *,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterable[Predictor]:
        """List non-archived Predictors."""
        return self._paginator.paginate(page_fetcher=self._fetch_page,
                                        collection_builder=self._build_unarchived_collection,
                                        page=page,
                                        per_page=per_page)

    def list_archived(self,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 20) -> Iterable[Predictor]:
        """List archived Predictors."""
        fetcher = partial(self._fetch_page, additional_params={"filter": "archived eq 'true'"})

        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_archived_collection,
                                        page=page,
                                        per_page=per_page)

    def check_for_update(self, uid: Union[UUID, str] = None,
                         predictor_id: Union[UUID, str] = None) -> Optional[Predictor]:
        """
        Check if there are updates available for a predictor.

        Typically these are updates to the training data. For example, a GEM Table may have
        been re-built to include additional rows.

        This check does not update the predictor; it just returns the update that is available.
        To perform the update, the response should then be used to call PredictorCollection.update

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the predictor to check
        predictor_id: Union[UUID, str]
            [DEPRECATED] please use uid instead

        Returns
        -------
        Optional[Predictor]
            The update, if an update is available; None otherwise.

        """
        uid = migrate_deprecated_argument(uid, "uid", predictor_id, "predictor_id")
        path = self._predictors_path("update-check", uid)
        update_data = self.session.get_resource(path, version=self._api_version)
        if update_data["updatable"]:
            built = Predictor.build(update_data)
            built.uid = uid
            return self._inject_archive_info(built)
        else:
            return None

    def auto_configure(self,
                       *,
                       training_data: DataSource,
                       pattern: Union[str, AutoConfigureMode] = AutoConfigureMode.INFER,
                       prefer_valid: bool = True) -> Predictor:
        """[ALPHA] Create a default predictor for some training data.

        This method will return an unregistered predictor generated by inspecting the
        training data and attempting to automatically configure the predictor.

        The configuration generated while using the `AutoConfigureMode.SIMPLE` pattern
        includes featurizers for chemical formulas/molecular structures,
        and `AutoMLPredictor`s for any variables identified as responses in the training data.
        The configuration generated while using the `AutoConfigureMode.FORMULATION` pattern
        includes these same components, as well as a `SimpleMixturePredictor`,
        `LabelFractionsPredictor`, `IngredientFractionsPredictor`, and a series of
        `MeanPropertyPredictor`s to handle featurization of formulation quantities
        and ingredient properties.
        The `AutoConfigureMode.INFER` pattern chooses an appropriate mode based on whether
        the data source contains formulations data or not.

        Parameters
        ----------
        training_data: DataSource
            The data to configure the predictor to model.
        pattern: AutoConfigureMode or str
            The predictor pattern to use, either "PLAIN", "FORMULATION", or "INFER".
            The "INFER" pattern auto-detects whether the `DataSource` contains formulations
            data or not.
            If it does, then a formulation predictor is created.
            If not, then a plain predictor is created.
        prefer_valid: Boolean
            If True, enables filtering of sparse descriptors and trimming of
            excess graph components in attempt to return a default configuration
            that will pass validation.
            Default: True.

        Returns
        -------
        Predictor
            Automatically configured predictor for the training data

        """
        # Continue handling string pattern inputs
        if not isinstance(pattern, AutoConfigureMode):
            pattern = AutoConfigureMode.get_enum(pattern)
        pattern = pattern.value

        path = self._predictors_path("default")
        body = {"data_source": training_data.dump(), "pattern": pattern,
                "prefer_valid": prefer_valid}
        data = self.session.post_resource(path, json=body, version=self._api_version)
        predictor = self.build(Predictor.wrap_instance(data["instance"]))
        return self._inject_archive_info(predictor)

    def convert_to_graph(self, uid: Union[UUID, str], retrain_if_needed: bool = False) \
            -> Predictor:
        """Given a SimpleML or Graph predictor, get an equivalent Graph predictor.

        Returns a Graph predictor with any SimpleML predictors converted to an equivalent AutoML
        predictor. If it's not a SimpleML or Graph predictor, or it's not in the READY state, an
        error is raised. SimpleML predictors are deprecated, so this is to aid in your migration.

        Note this conversion is not performed in place! That is, the predictor returned is not
        persisted on the platform. To persist it, pass the converted predictor to
        :py:meth:`citrine.resources.project.PredictorCollection.update`. Or you can do this in
        one step with :py:meth:`citrine.resources.project.PredictorCollection.convert_and_update`.

        .. code:: python

            converted = project.predictors.convert_to_graph(predictor_uid)
            project.predictors.update(converted)

            # is equivalent to

            converted = project.predictors.convert_and_update(predictor_uid)

        If a predictor needs to be retrained before conversion, it will raise an HTTP 409 Conflict
        error. This may occur when the Citrine Platform has been updated since your predictor was
        last trained. If `retrain_if_needed` is `True`, retraining will automatically begin, and
        the method will return `None. Once retraining completes, call this method again to get the
        converted predictor. For example:

        .. code:: python

            converted = project.predictors.convert_and_update(pred.uid, retrain_if_needed=True)
            if converted is None:
                predictor = project.predictors.get(pred.uid)
                wait_while_validating(collection=project.predictors, module=predictor)
                converted = project.predictors.convert_and_update(pred.uid)
        """
        path = self._predictors_path("convert", uid)
        try:
            entity = self.session.get_resource(path, version=self._api_version)
        except Conflict as exc:
            if retrain_if_needed:
                # Invokes super.get to avoid an extra call to _inject_archive_info.
                self.update(super().get(uid))
                return None
            else:
                raise exc
        predictor = self.build(entity)
        return self._inject_archive_info(predictor)

    def convert_and_update(self, uid: Union[UUID, str], retrain_if_needed: bool = False) \
            -> Predictor:
        """Given a SimpleML or Graph predictor, overwrite it with an equivalent Graph predictor.

        See `PredictorCollection.convert_to_graph` for more detail.
        """
        new_pred = self.convert_to_graph(uid, retrain_if_needed)
        return self.update(new_pred) if new_pred else None
