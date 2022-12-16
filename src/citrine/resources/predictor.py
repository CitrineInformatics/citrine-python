"""Resources that represent collections of predictors."""
from functools import partial
from typing import Any, Iterable, Optional, TypeVar, Union
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.paginator import Paginator
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument, format_escaped_url
from citrine.exceptions import Conflict
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors import Predictor
from citrine.resources.module import AbstractModuleCollection

from deprecation import deprecated

CreationType = TypeVar('CreationType', bound=Predictor)


MOST_RECENT_VER = "most_recent"


class AutoConfigureMode(BaseEnumeration):
    """[ALPHA] The format to use in building auto-configured assets.

    * PLAIN corresponds to a single-row GEM table and plain predictor
    * FORMULATION corresponds to a multi-row GEM table and formulations predictor
    * INFER auto-detects the GEM table and predictor type
    """

    PLAIN = 'PLAIN'
    FORMULATION = 'FORMULATION'
    INFER = 'INFER'


class _PredictorVersionPaginator(Paginator):
    def _comparison_fields(self, entity: Predictor) -> Any:
        return (entity.uid, entity.version)

    def paginate(self, *args, **kwargs) -> Iterable[Predictor]:
        # Since predictor versions have the same uid, and the paginate method uses uid alone to
        # dedup, we have to disable deduplication in order to use it.
        kwargs["deduplicate"] = False
        return super().paginate(*args, **kwargs)


class _PredictorVersionCollection(AbstractModuleCollection[Predictor]):
    _api_version = 'v3'
    _path_template = '/projects/{project_id}/predictors/{uid}/versions'
    _individual_key = None
    _resource = Predictor
    _collection_key = 'response'
    _paginator: Paginator = _PredictorVersionPaginator()

    _SPECIAL_VERSIONS = ["latest", MOST_RECENT_VER]

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def _construct_path(self,
                        uid: Union[UUID, str],
                        version: Optional[Union[int, str]] = None,
                        action: str = None) -> str:
        path = self._path_template.format(project_id=self.project_id, uid=str(uid))
        if version is not None:
            version_str = str(version)
            if version_str not in self._SPECIAL_VERSIONS \
                    and (not version_str.isdecimal() or int(version_str) <= 0):
                raise ValueError("A predictor version must either be a positive integer, "
                                 f"\"latest\", or \"{MOST_RECENT_VER}\".")

            path += f"/{version_str}"
            path += f"/{action}" if action else ""
        return path

    def _page_fetcher(self, *, uid: Union[UUID, str], **additional_params):
        fetcher_params = {
            "path": self._construct_path(uid),
            "additional_params": additional_params
        }
        return partial(self._fetch_page, **fetcher_params)

    def _train(self, uid: Union[UUID, str], version: Union[int, str]) -> Predictor:
        path = self._construct_path(uid, version, "train")
        params = {"create_version": True}
        entity = self.session.put_resource(path, {}, params=params, version=self._api_version)
        return self.build(entity)

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor: Predictor = Predictor.build(data)
        predictor._session = self.session
        predictor._project_id = self.project_id
        return predictor

    def get(self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER) -> Predictor:
        path = self._construct_path(uid, version)
        entity = self.session.get_resource(path, version=self._api_version)
        return self.build(entity)

    def list(self,
             uid: Union[UUID, str],
             *,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterable[Predictor]:
        """List non-archived versions of the given predictor."""
        page_fetcher = self._page_fetcher(uid=uid)
        return self._paginator.paginate(page_fetcher=page_fetcher,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def list_archived(self,
                      uid: Union[UUID, str],
                      *,
                      page: Optional[int] = None,
                      per_page: int = 20) -> Iterable[Predictor]:
        """List archived versions of the given predictor."""
        page_fetcher = self._page_fetcher(uid=uid, filter="archived eq 'true'")
        return self._paginator.paginate(page_fetcher=page_fetcher,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def archive(self, uid: Union[UUID, str], *, version: Union[int, str] = MOST_RECENT_VER):
        url = self._construct_path(uid, version, "archive")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def restore(self, uid: Union[UUID, str], *, version: Union[int, str] = MOST_RECENT_VER):
        url = self._construct_path(uid, version, "restore")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def convert_to_graph(self,
                         uid: Union[UUID, str],
                         *,
                         version: Union[int, str] = MOST_RECENT_VER,
                         retrain_if_needed: bool = False) -> Predictor:
        path = self._construct_path(uid, version, "convert")
        try:
            entity = self.session.get_resource(path, version=self._api_version)
        except Conflict as exc:
            if retrain_if_needed:
                self._train(uid, version)
                return None
            else:
                raise exc
        return self.build(entity)


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
        self._versions_collection = _PredictorVersionCollection(project_id, session)

    def _predictors_path(self, subpath: str, uid: Union[UUID, str] = None) -> str:
        path_template = self._path_template + (f"/{uid}" if uid else "") + f"/{subpath}"
        return format_escaped_url(path_template, project_id=self.project_id)

    def build(self, data: dict) -> Predictor:
        """Build an individual Predictor."""
        predictor: Predictor = Predictor.build(data)
        predictor._session = self.session
        predictor._project_id = self.project_id
        return predictor

    def get(self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER) -> Predictor:
        """Get a predictor by ID and (optionally) version.

        If version is omitted, the most recent version will be retrieved.
        """
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        return self._versions_collection.get(uid=uid, version=version)

    def register(self, predictor: Predictor) -> Predictor:
        """Register and train a Predictor.

        This predctor will be version 1, and its `draft` flag will be `True`. If training completes
        successfully, the `draft` flag will be set to `False`. Otherwise, it will remain `False`.
        """
        created_predictor = super().register(predictor)

        # If the initial response is invalid, just return it.
        # If not, kick off training since we never exposed saving a model without it,
        # so we should continue to do it automatically.
        if created_predictor.failed():
            return created_predictor
        else:
            return self._train(created_predictor.uid)

    def update(self, predictor: Predictor) -> Predictor:
        """Update and train a Predictor.

        If the predictor is a draft, this will overwrite its contents, then begin training. If it's
        not a draft, a new version will be created with the update, and then training will begin.

        In either case, if training completes successfully, it will no longer be a draft.
        """
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
        params = {"create_version": True}
        entity = self.session.put_resource(path, {}, params=params, version=self._api_version)
        return self.build(entity)

    def archive_version(self, uid: Union[UUID, str], *, version: Union[int, str]) -> Predictor:
        """Archive a predictor version."""
        return self._versions_collection.archive(uid, version=version)

    def restore_version(self, uid: Union[UUID, str], *, version: Union[int, str]) -> Predictor:
        """Restore a predictor version."""
        return self._versions_collection.restore(uid, version=version)

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

    def list_versions(self,
                      uid: Union[UUID, str] = None,
                      *,
                      per_page: int = 100) -> Iterable[Predictor]:
        """List all non-archived versions of the given Predictor."""
        return self._versions_collection.list(uid, per_page=per_page)

    def list_archived(self,
                      *,
                      page: Optional[int] = None,
                      per_page: int = 20) -> Iterable[Predictor]:
        """List archived Predictors."""
        fetcher = partial(self._fetch_page, additional_params={"filter": "archived eq 'true'"})
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        page=page,
                                        per_page=per_page)

    def list_archived_versions(self,
                               uid: Union[UUID, str] = None,
                               *,
                               per_page: int = 20) -> Iterable[Predictor]:
        """List all archived versions of the given Predictor."""
        return self._versions_collection.list_archived(uid, per_page=per_page)

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
            return built
        else:
            return None

    def create_default(self,
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
        return self.build(Predictor.wrap_instance(data["instance"]))

    def convert_to_graph(self,
                         uid: Union[UUID, str],
                         retrain_if_needed: bool = False,
                         *,
                         version: Union[int, str] = MOST_RECENT_VER) -> Predictor:
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
        return self._versions_collection.convert_to_graph(uid,
                                                          version=version,
                                                          retrain_if_needed=retrain_if_needed)

    def convert_and_update(self,
                           uid: Union[UUID, str],
                           retrain_if_needed: bool = False,
                           *,
                           version: Union[int, str] = MOST_RECENT_VER) -> Predictor:
        """Given a SimpleML or Graph predictor, overwrite it with an equivalent Graph predictor.

        See `PredictorCollection.convert_to_graph` for more detail.
        """
        new_pred = self.convert_to_graph(uid, version=version, retrain_if_needed=retrain_if_needed)
        return self.update(new_pred) if new_pred else None

    @deprecated(deprecated_in="1.50.0", removed_in="2.0.0",
                details="Use PredictorCollection.get() instead.")
    def get_version(self, uid: Union[UUID, str], *, version: Union[int, str]) -> Predictor:
        """[DEPRECATED] Get a specific version of the predictor."""
        return self.get(uid=uid, version=version)

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

    @deprecated(deprecated_in="1.47.0", removed_in="2.0.0",
                details="auto_configure is an alias for create_default.")
    def auto_configure(self,
                       *,
                       training_data: DataSource,
                       pattern: Union[str, AutoConfigureMode] = AutoConfigureMode.INFER,
                       prefer_valid: bool = True) -> Predictor:
        """[DEPRECATED] Alias for PredictorCollection.create_default."""
        return self.create_default(training_data=training_data, pattern=pattern,
                                   prefer_valid=prefer_valid)

    @deprecated(deprecated_in="1.50.0", removed_in="2.0.0",
                details="Use PredictorCollection.convert_to_graph() instead.")
    def convert_version_to_graph(self,
                                 uid: Union[UUID, str],
                                 *,
                                 version: Union[int, str],
                                 retrain_if_needed: bool = False) -> Predictor:
        """[DEPRECATED] Given a SimpleML or Graph predictor, get an equivalent Graph predictor.

        See `PredictorCollection.convert_to_graph` for more detail.
        """
        return self.convert_to_graph(uid, version=version, retrain_if_needed=retrain_if_needed)

    @deprecated(deprecated_in="1.50.0", removed_in="2.0.0",
                details="Use PredictorCollection.convert_and_update() instead.")
    def convert_version_and_update(self,
                                   uid: Union[UUID, str],
                                   *,
                                   version: Union[int, str],
                                   retrain_if_needed: bool = False) -> Predictor:
        """[DEPRECATED] Overwrite a SimpleML or Graph predictor with an equivalent Graph predictor.

        See `PredictorCollection.convert_to_graph` for more detail.
        """
        return self.convert_and_update(uid, version=version, retrain_if_needed=retrain_if_needed)
