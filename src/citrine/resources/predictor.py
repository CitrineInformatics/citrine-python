"""Resources that represent collections of predictors."""
from functools import partial
from typing import Any, Iterable, Optional, Union, List
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._rest.paginator import Paginator
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_candidate import HierarchicalDesignMaterial
from citrine.informatics.executions.predictor_evaluation import PredictorEvaluation
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.predictors import GraphPredictor
from citrine.resources.status_detail import StatusDetail


# The most recently edited prediction version. Could be a draft.
MOST_RECENT_VER = "most_recent"
# The highest trained predictor version.
LATEST_VER = "latest"


class EvaluatorsPayload(Serializable['EvaluatorsPayload']):
    """Container object for predictor evaluators."""

    evaluators = properties.List(properties.Object(PredictorEvaluator), "evaluators")

    def __init__(self, evaluators):
        self.evaluators = evaluators


class AsyncDefaultPredictor(Resource["AsyncDefaultPredictor"]):
    """Return type for async default predictor generation and retrieval."""

    uid = properties.UUID('id', serializable=False)
    """:UUID: Citrine Platform unique identifier for this task."""

    predictor = properties.Optional(properties.Object(GraphPredictor), 'data', serializable=False)
    """:Optional[GraphPredictor]:"""

    status = properties.String('metadata.status', serializable=False)
    """:str: short description of the resource's status"""

    status_detail = properties.List(properties.Object(StatusDetail), 'metadata.status_detail',
                                    default=[], serializable=False)
    """:List[StatusDetail]: a list of structured status info, containing the message and level"""

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Build an instance of this object from given data."""
        if data.get("data"):
            data["data"] = GraphPredictor.wrap_instance(data["data"]["instance"])
        return data


class AutoConfigureMode(BaseEnumeration):
    """The format to use in building auto-configured assets.

    * PLAIN corresponds to a single-row GEM table and plain predictor
    * FORMULATION corresponds to a multi-row GEM table and formulations predictor
    * INFER auto-detects the GEM table and predictor type
    """

    PLAIN = 'PLAIN'
    FORMULATION = 'FORMULATION'
    INFER = 'INFER'


class _PredictorVersionPaginator(Paginator):
    def _comparison_fields(self, entity: GraphPredictor) -> Any:
        return (entity.uid, entity.version)

    def paginate(self, *args, **kwargs) -> Iterable[GraphPredictor]:
        # Since predictor versions have the same uid, and the paginate method uses uid alone to
        # dedup, we have to disable deduplication in order to use it.
        kwargs["deduplicate"] = False
        return super().paginate(*args, **kwargs)


class _PredictorVersionCollection(Collection[GraphPredictor]):
    _api_version = 'v3'
    _path_template = '/projects/{project_id}/predictors/{uid}/versions'
    _individual_key = None
    _resource = GraphPredictor
    _collection_key = 'response'
    _paginator: Paginator = _PredictorVersionPaginator()

    _SPECIAL_VERSIONS = [LATEST_VER, MOST_RECENT_VER]

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
                                 f"\"{LATEST_VER}\", or \"{MOST_RECENT_VER}\".")

            path += f"/{version_str}"
            path += f"/{action}" if action else ""
        return path

    def _page_fetcher(self, *, uid: Union[UUID, str], **additional_params):
        fetcher_params = {
            "path": self._construct_path(uid),
            "additional_params": additional_params
        }
        return partial(self._fetch_page, **fetcher_params)

    def build(self, data: dict) -> GraphPredictor:
        """Build an individual Predictor."""
        predictor: GraphPredictor = GraphPredictor.build(data)
        predictor._session = self.session
        predictor._project_id = self.project_id
        return predictor

    def get(self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER) -> GraphPredictor:
        path = self._construct_path(uid, version)
        entity = self.session.get_resource(path, version=self._api_version)
        return self.build(entity)

    def get_featurized_training_data(
            self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER
    ) -> List[HierarchicalDesignMaterial]:
        version_path = self._construct_path(uid, version)
        full_path = f"{version_path}/featurized-training-data"
        payload = self.session.get_resource(full_path, version=self._api_version)
        return [HierarchicalDesignMaterial.build(x) for x in payload]

    def list(self,
             uid: Union[UUID, str],
             *,
             per_page: int = 100) -> Iterable[GraphPredictor]:
        """List non-archived versions of the given predictor."""
        page_fetcher = self._page_fetcher(uid=uid)
        return self._paginator.paginate(page_fetcher=page_fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list_archived(self,
                      uid: Union[UUID, str],
                      *,
                      per_page: int = 20) -> Iterable[GraphPredictor]:
        """List archived versions of the given predictor."""
        page_fetcher = self._page_fetcher(uid=uid, filter="archived eq 'true'")
        return self._paginator.paginate(page_fetcher=page_fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def archive(self,
                uid: Union[UUID, str],
                *,
                version: Union[int, str] = MOST_RECENT_VER) -> GraphPredictor:
        url = self._construct_path(uid, version, "archive")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def restore(self,
                uid: Union[UUID, str],
                *,
                version: Union[int, str] = MOST_RECENT_VER) -> GraphPredictor:
        url = self._construct_path(uid, version, "restore")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def is_stale(self,
                 uid: Union[UUID, str],
                 *,
                 version: Union[int, str] = MOST_RECENT_VER) -> bool:
        path = self._construct_path(uid, version, "is-stale")
        response = self.session.get_resource(path, version=self._api_version)
        return response["is_stale"]

    def retrain_stale(self,
                      uid: Union[UUID, str],
                      *,
                      version: Union[int, str] = MOST_RECENT_VER) -> GraphPredictor:
        path = self._construct_path(uid, version, "retrain-stale")
        entity = self.session.put_resource(path, {}, version=self._api_version)
        return self.build(entity)

    def rename(self,
               uid: Union[UUID, str],
               *,
               version: Union[int, str],
               name: Optional[str] = None,
               description: Optional[str] = None
               ) -> GraphPredictor:
        path = self._construct_path(uid, version, "rename")
        json = {"name": name, "description": description}
        entity = self.session.put_resource(path, json, version=self._api_version)
        return self.build(entity)

    def default_evaluators(self,
                           uid: Union[UUID, str],
                           *,
                           version: Union[int, str]) -> List[PredictorEvaluator]:
        path = self._construct_path(uid, version, action="default-evaluators")
        evaluators = self.session.get_resource(path)
        return EvaluatorsPayload.build(evaluators).evaluators

    def _build_predictor_evaluation(self, data):
        evaluation = PredictorEvaluation.build(data)
        evaluation.project_id = self.project_id
        evaluation._session = self.session
        return evaluation

    def evaluate(self,
                 uid: Union[UUID, str],
                 *,
                 version: Union[int, str],
                 evaluators: List[PredictorEvaluator]) -> PredictorEvaluation:
        path = self._construct_path(uid, version, "evaluate")
        payload = EvaluatorsPayload(evaluators=evaluators).dump()
        response = self.session.post_resource(path, payload, version=self._api_version)
        return self._build_predictor_evaluation(response)

    def evaluate_default(self,
                         uid: Union[UUID, str],
                         *,
                         version: Union[int, str]) -> PredictorEvaluation:
        path = self._construct_path(uid, version, "evaluate-default")
        response = self.session.post_resource(path, {}, version=self._api_version)
        return self._build_predictor_evaluation(response)

    def delete(self, uid: Union[UUID, str], *, version: Union[int, str] = MOST_RECENT_VER):
        """Predictor versions cannot be deleted at this time."""
        msg = "Predictor versions cannot be deleted. Use 'archive_version' instead."
        raise NotImplementedError(msg)


class PredictorCollection(Collection[GraphPredictor]):
    """Represents the collection of all predictors for a project.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _api_version = 'v3'
    _path_template = '/projects/{project_id}/predictors'
    _individual_key = None
    _resource = GraphPredictor
    _collection_key = 'response'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session
        self._versions_collection = _PredictorVersionCollection(project_id, session)

    def build(self, data: dict) -> GraphPredictor:
        """Build an individual Predictor."""
        predictor: GraphPredictor = GraphPredictor.build(data)
        predictor._session = self.session
        predictor._project_id = self.project_id
        return predictor

    def get(self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER) -> GraphPredictor:
        """Get a predictor by ID and (optionally) version.

        If version is omitted, the most recent version will be retrieved.
        """
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        return self._versions_collection.get(uid=uid, version=version)

    def get_featurized_training_data(
            self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str] = MOST_RECENT_VER
    ) -> List[HierarchicalDesignMaterial]:
        """Retrieve a list of featurized materials for a trained predictor.

        Featurized materials contain the input variables found in the training data source
        along with any internal features generated by the predictor while training.
        If not available, retraining the predictor will generate new featurized data.

        Parameters
        ----------
        uid: UUID
            the UUID of the predictor
        version: str
            the version of the predictor (if omitted, the most recent will be used)

        Returns
        -------
        A list of featurized materials, formatted as design materials

        """
        return self._versions_collection.get_featurized_training_data(uid=uid, version=version)

    def register(self, predictor: GraphPredictor, *, train: bool = True) -> GraphPredictor:
        """Register and optionally train a Predictor.

        This predctor will be version 1, and its `draft` flag will be `True`. If train is True and
        training completes successfully, the `draft` flag will be set to `False`. Otherwise, it
        will remain `True`.
        """
        created_predictor = super().register(predictor)

        if not train or created_predictor.failed():
            return created_predictor
        else:
            return self.train(created_predictor.uid)

    def update(self, predictor: GraphPredictor, *, train: bool = True) -> GraphPredictor:
        """Update and optionally train a Predictor.

        If the predictor is a draft, this will overwrite its contents. If it's not a draft, a new
        version will be created with the update.

        In either case, training will begin after the update if train is `True`. And if training
        completes successfully, the Predictor will no longer be a draft.
        """
        updated_predictor = super().update(predictor)

        if not train or updated_predictor.failed():
            return updated_predictor
        else:
            return self.train(updated_predictor.uid)

    def train(self, uid: Union[UUID, str]) -> GraphPredictor:
        """Train a predictor.

        If the predictor is not a draft, a new version will be created which is a copy of the
        current predictor version as a draft, which will be trained. Either way, if training
        completes successfully, the Predictor will no longer be a draft.
        """
        path = self._get_path(uid, action="train")
        params = {"create_version": True}
        entity = self.session.put_resource(path, {}, params=params, version=self._api_version)
        return self.build(entity)

    def archive_version(
            self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str]
    ) -> GraphPredictor:
        """Archive a predictor version."""
        return self._versions_collection.archive(uid, version=version)

    def restore_version(
            self,
            uid: Union[UUID, str],
            *,
            version: Union[int, str]
    ) -> GraphPredictor:
        """Restore a predictor version."""
        return self._versions_collection.restore(uid, version=version)

    def archive_root(self, uid: Union[UUID, str]):
        """Archive a root predictor.

        uid: Union[UUID, str]
            Unique identifier of the predictor to archive.

        """
        path = self._get_path(uid=uid, action="archive")
        self.session.put_resource(path, {}, version=self._api_version)

    def restore_root(self, uid: Union[UUID, str]):
        """Restore an archived root predictor.

        uid: Union[UUID, str]
            Unique identifier of the predictor to restore.

        """
        path = self._get_path(uid, action="restore")
        self.session.put_resource(path, {}, version=self._api_version)

    def root_is_archived(self, uid: Union[UUID, str]) -> bool:
        """Determine if the predictor root is archived.

        uid: Union[UUID, str]
            Unique identifier of the predictor to check.
        """
        uid = str(uid)
        return any(uid == str(archived_pred.uid) for archived_pred in self.list_archived())

    def archive(self, uid: Union[UUID, str]):
        """[UNSUPPORTED] Use archive_root or archive_version instead."""
        raise NotImplementedError("The archive() method is no longer supported. You most likely "
                                  "want archive_root(), or possibly archive_version().")

    def restore(self, uid: Union[UUID, str]):
        """[UNSUPPORTED] Use restore_root or restore_version instead."""
        raise NotImplementedError("The restore() method is no longer supported. You most likely "
                                  "want restore_root(), or possibly restore_version().")

    def _list_base(self, *, per_page: int = 100, archived: Optional[bool] = None):
        filters = {}
        if archived is not None:
            filters["archived"] = archived

        fetcher = partial(self._fetch_page,
                          additional_params=filters,
                          version="v4")
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list_all(self, *, per_page: int = 20) -> Iterable[GraphPredictor]:
        """List the most recent version of all predictors."""
        return self._list_base(per_page=per_page)

    def list(self, *, per_page: int = 20) -> Iterable[GraphPredictor]:
        """List the most recent version of all non-archived predictors."""
        return self._list_base(per_page=per_page, archived=False)

    def list_archived(self, *, per_page: int = 20) -> Iterable[GraphPredictor]:
        """List the most recent version of all archived predictors."""
        return self._list_base(per_page=per_page, archived=True)

    def list_versions(self,
                      uid: Union[UUID, str] = None,
                      *,
                      per_page: int = 100) -> Iterable[GraphPredictor]:
        """List all non-archived versions of the given Predictor."""
        return self._versions_collection.list(uid, per_page=per_page)

    def list_archived_versions(self,
                               uid: Union[UUID, str] = None,
                               *,
                               per_page: int = 20) -> Iterable[GraphPredictor]:
        """List all archived versions of the given Predictor."""
        return self._versions_collection.list_archived(uid, per_page=per_page)

    def check_for_update(self, uid: Union[UUID, str]) -> Optional[GraphPredictor]:
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

        Returns
        -------
        Optional[Predictor]
            The update, if an update is available; None otherwise.

        """
        path = self._get_path(uid, action="update-check")
        update_data = self.session.get_resource(path, version=self._api_version)
        if update_data["updatable"]:
            built = GraphPredictor.build(update_data)
            built.uid = uid
            return built
        else:
            return None

    def create_default(self,
                       *,
                       training_data: DataSource,
                       pattern: Union[str, AutoConfigureMode] = AutoConfigureMode.INFER,
                       prefer_valid: bool = True) -> GraphPredictor:
        """Create a default predictor for some training data.

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
        GraphPredictor
            Automatically configured predictor for the training data

        """
        payload = PredictorCollection._create_default_payload(training_data, pattern, prefer_valid)
        path = self._get_path(action="default")
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return self.build(GraphPredictor.wrap_instance(data["instance"]))

    def create_default_async(self,
                             *,
                             training_data: DataSource,
                             pattern: Union[str, AutoConfigureMode] = AutoConfigureMode.INFER,
                             prefer_valid: bool = True) -> AsyncDefaultPredictor:
        """Similar to PredictorCollection.create_default, except asynchronous.

        This begins a long-running task to generate the predictor. The returned object contains an
        ID which can be used to track its status and get the resulting predictor once complete.
        PredictorCollection.get_default_async is intended for that purpose.

        See PredictorCollection.create_default for more details on the generation process and
        parameter specifics.

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
        AsyncDefaultPredictor
            Information on the long-running default predictor generation task.

        """
        payload = PredictorCollection._create_default_payload(training_data, pattern, prefer_valid)
        path = self._get_path(action="default-async")
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return AsyncDefaultPredictor.build(data)

    @staticmethod
    def _create_default_payload(training_data: DataSource,
                                pattern: Union[str, AutoConfigureMode] = AutoConfigureMode.INFER,
                                prefer_valid: bool = True) -> dict:
        # Continue handling string pattern inputs
        pattern = AutoConfigureMode.from_str(pattern, exception=True)

        return {"data_source": training_data.dump(), "pattern": pattern,
                "prefer_valid": prefer_valid}

    def get_default_async(self, *, task_id: Union[UUID, str]) -> AsyncDefaultPredictor:
        """Get the current async default predictor generation result.

        The status field will indicate if it's INPROGRESS, SUCCEEDED, or FAILED. While INPROGRESS,
        the predictor will also be None. Once it's SUCCEEDED, it will be populated with a
        GraphPredictor, which can then be registered to the platform. If it's FAILED, look to the
        status_detail field for more information on what went wrong.
        """
        path = self._get_path(action=["default-async", task_id])
        data = self.session.get_resource(path, version=self._api_version)
        return AsyncDefaultPredictor.build(data)

    def is_stale(self, uid: Union[UUID, str], *, version: Union[int, str]) -> bool:
        """Returns True if a predictor is stale, False otherwise.

        A predictor is stale if it's in the READY state, but the platform cannot load the
        previously trained object.
        """
        return self._versions_collection.is_stale(uid, version=version)

    def retrain_stale(self, uid: Union[UUID, str], *, version: Union[int, str]) -> GraphPredictor:
        """Begins retraining a stale predictor.

        This can only be used on a stale predictor, which is when it's in the READY state, but the
        platform cannot load the previously trained object. Using it on a non-stale predictor will
        result in an error.
        """
        return self._versions_collection.retrain_stale(uid, version=version)

    def rename(self,
               uid: Union[UUID, str],
               *,
               version: Union[int, str],
               name: Optional[str] = None,
               description: Optional[str] = None) -> GraphPredictor:
        """Rename an existing predictor.

        Both the name and description can be changed. This does not trigger retraining.
        Any existing version of the predictor can be renamed, or "most_recent".
        """
        return self._versions_collection.rename(
            uid, version=version, name=name, description=description
        )

    def default_evaluators_from_config(self,
                                       predictor: GraphPredictor) -> List[PredictorEvaluator]:
        """Retrieve the default evaluators for an arbitrary (but valid) predictor config.

        See :func:`~citrine.resources.PredictorCollection.default_evaluators` for details on the
        evaluators.
        """
        path = self._get_path(action="default-evaluators-from-config")
        payload = predictor.dump()
        evaluators = self.session.post_resource(path, json=payload, version=self._api_version)
        return EvaluatorsPayload.build(evaluators).evaluators

    def default_evaluators(self,
                           uid: Union[UUID, str],
                           *,
                           version: Union[int, str] = MOST_RECENT_VER) -> List[PredictorEvaluator]:
        """Retrieve the default evaluators for a stored predictor.

        The current default evaluators perform 5-fold, 3-trial cross-validation on all valid
        predictor responses. Valid responses are those that are **not** produced by the
        following predictors:

        * :class:`~citrine.informatics.predictors.generalized_mean_property_predictor.GeneralizedMeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.mean_property_predictor.MeanPropertyPredictor`
        * :class:`~citrine.informatics.predictors.ingredient_fractions_predictor.IngredientFractionsPredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_simple_mixture_predictor.IngredientsToSimpleMixturePredictor`
        * :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor`
        * :class:`~citrine.informatics.predictors.label_fractions_predictor.LabelFractionsPredictor`
        * :class:`~citrine.informatics.predictors.molecular_structure_featurizer.MolecularStructureFeaturizer`
        * :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor`

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate

        Returns
        -------
        PredictorEvaluation

        """  # noqa: E501,W505
        return self._versions_collection.default_evaluators(uid, version=version)

    def evaluate(self,
                 uid: Union[UUID, str],
                 *,
                 version: Union[int, str] = LATEST_VER,
                 evaluators: List[PredictorEvaluator]) -> PredictorEvaluation:
        """Evaluate a predictor using the provided evaluators.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate. Defaults to the latest trained version.
        evaluators: list

        Returns
        -------
        PredictorEvaluation

        """
        return self._versions_collection.evaluate(uid, version=version, evaluators=evaluators)

    def evaluate_default(self,
                         uid: Union[UUID, str],
                         *,
                         version: Union[int, str] = MOST_RECENT_VER) -> PredictorEvaluation:
        """Evaluate a predictor using the default evaluators.

        See :func:`~citrine.resources.PredictorCollection.default_evaluators` for details on the evaluators.

        Parameters
        ----------
        predictor_id: UUID
            Unique identifier of the predictor to evaluate
        predictor_version: Option[Union[int, str]]
            The version of the predictor to evaluate

        Returns
        -------
        PredictorEvaluation

        """  # noqa: E501,W505
        return self._versions_collection.evaluate_default(uid, version=version)

    def delete(self, uid: Union[UUID, str]):
        """Predictors cannot be deleted at this time."""
        msg = "Predictors cannot be deleted. Use 'archive_version' or 'archive_root' instead."
        raise NotImplementedError(msg)
