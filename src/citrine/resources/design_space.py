"""Resources that represent collections of design spaces."""
import warnings
from functools import partial
from typing import Iterable, Iterator, Optional, TypeVar, Union
from uuid import UUID


from citrine._utils.functions import format_escaped_url
from citrine.informatics.design_spaces import DataSourceDesignSpace, DefaultDesignSpaceMode, \
    DesignSpace, DesignSpaceSettings, EnumeratedDesignSpace, FormulationDesignSpace, \
    HierarchicalDesignSpace
from citrine._rest.collection import Collection
from citrine._session import Session

CreationType = TypeVar('CreationType', bound=DesignSpace)


class DesignSpaceCollection(Collection[DesignSpace]):
    """Represents the collection of design spaces as well as the resources belonging to it.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _api_version = 'v3'
    _path_template = '/projects/{project_id}/design-spaces'
    _individual_key = None
    _resource = DesignSpace
    _collection_key = 'response'
    _enumerated_cell_limit = 128 * 2000

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> DesignSpace:
        """Build an individual design space."""
        design_space: DesignSpace = DesignSpace.build(data)
        design_space._session = self.session
        design_space._project_id = self.project_id
        return design_space

    def _verify_write_request(self, design_space: DesignSpace):
        """Perform write-time validations of the design space registration or update.

        EnumeratedDesignSpaces can be pretty big, so we want to return a helpful error message
        rather than let the POST or PUT call fail because the request body is too big.  This
        validation is performed when the design space is sent to the platform in case a user
        creates a large intermediate design space but then filters it down before registering it.

        Additionally, checks for deprecated top-level design space types, and emits deprecation
        warnings as appropriate.
        """
        if isinstance(design_space, EnumeratedDesignSpace):
            warnings.warn("As of 3.27.0, EnumeratedDesignSpace is deprecated in favor of a "
                          "ProductDesignSpace containing a DataSourceDesignSpace subspace. "
                          "Support for EnumeratedDesignSpace will be dropped in 4.0.",
                          DeprecationWarning)

            width = len(design_space.descriptors)
            length = len(design_space.data)
            if width * length > self._enumerated_cell_limit:
                msg = "EnumeratedDesignSpace only supports up to {} descriptor-values, " \
                      "but {} were given. Please reduce the number of descriptors or candidates " \
                      "in this EnumeratedDesignSpace"
                raise ValueError(msg.format(self._enumerated_cell_limit, width * length))
        elif isinstance(design_space, (DataSourceDesignSpace, FormulationDesignSpace)):
            typ = type(design_space).__name__
            warnings.warn(f"As of 3.27.0, saving a top-level {typ} is deprecated. Support "
                          "will be removed in 4.0. Wrap it in a ProductDesignSpace instead: "
                          f"ProductDesignSpace('name', 'description', subspaces=[{typ}(...)])",
                          DeprecationWarning)

    def _verify_read_request(self, design_space: DesignSpace):
        """Perform read-time validations of the design space.

        Checks for deprecated top-level design space types, and emits deprecation warnings as
        appropriate.
        """
        if isinstance(design_space, EnumeratedDesignSpace):
            warnings.warn("As of 3.27.0, EnumeratedDesignSpace is deprecated in favor of a "
                          "ProductDesignSpace containing a DataSourceDesignSpace subspace. "
                          "Support for EnumeratedDesignSpace will be dropped in 4.0.",
                          DeprecationWarning)
        elif isinstance(design_space, (DataSourceDesignSpace, FormulationDesignSpace)):
            typ = type(design_space).__name__
            warnings.warn(f"As of 3.27.0, top-level {typ}s are deprecated. Any that remain when "
                          "SDK 4.0 are released will be wrapped in a ProductDesignSpace. You "
                          "can wrap it yourself to get rid of this warning now: "
                          f"ProductDesignSpace('name', 'description', subspaces=[{typ}(...)])",
                          DeprecationWarning)

    def register(self, design_space: DesignSpace) -> DesignSpace:
        """Create a new design space."""
        self._verify_write_request(design_space)

        registered_ds = super().register(design_space)

        # If the initial response is invalid, just return it.
        # If not, kick off validation, since we never exposed saving a design space without
        # validation so we should continue to do it automatically
        if registered_ds.failed():
            return registered_ds
        else:
            return self._validate(registered_ds.uid)

    def update(self, design_space: DesignSpace) -> DesignSpace:
        """Update and validate an existing DesignSpace."""
        self._verify_write_request(design_space)
        updated_ds = super().update(design_space)

        # If the initial response is invalid, just return it.
        # If not, kick off validation, since we never exposed saving a design space without
        # validation so we should continue to do it automatically
        if updated_ds.failed():
            return updated_ds
        else:
            return self._validate(updated_ds.uid)

    def _validate(self, uid: Union[UUID, str]) -> DesignSpace:
        path = self._get_path(uid, action="validate")
        entity = self.session.put_resource(path, {}, version=self._api_version)
        return self.build(entity)

    def archive(self, uid: Union[UUID, str]) -> DesignSpace:
        """Archiving a design space removes it from view, but is not a hard delete.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the design space to archive

        """
        url = self._get_path(uid, action="archive")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def restore(self, uid: Union[UUID, str]) -> DesignSpace:
        """Restore an archived design space.

        Parameters
        ----------
        uid: Union[UUID, str]
            Unique identifier of the design space to restore

        """
        url = self._get_path(uid, action="restore")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def get(self, uid: Union[UUID, str]) -> DesignSpace:
        """Get a particular element of the collection."""
        design_space = super().get(uid)
        self._verify_read_request(design_space)
        return design_space

    def _build_collection_elements(self, collection: Iterable[dict]) -> Iterator[DesignSpace]:
        """
        For each element in the collection, build the appropriate resource type.

        Parameters
        ---------
        collection: Iterable[dict]
            collection containing the elements to be built

        Returns
        -------
        Iterator[DesignSpace]
            Resources in this collection.

        """
        for design_space in super()._build_collection_elements(collection=collection):
            self._verify_read_request(design_space)
            yield design_space

    def _list_base(self, *, per_page: int = 100, archived: Optional[bool] = None):
        filters = {}
        if archived is not None:
            filters["archived"] = archived

        fetcher = partial(self._fetch_page, additional_params=filters, version="v4")
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list_all(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List all design spaces."""
        return self._list_base(per_page=per_page)

    def list(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List non-archived design spaces."""
        return self._list_base(per_page=per_page, archived=False)

    def list_archived(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List archived design spaces."""
        return self._list_base(per_page=per_page, archived=True)

    def create_default(self,
                       *,
                       predictor_id: Union[UUID, str],
                       predictor_version: Optional[Union[int, str]] = None,
                       mode: DefaultDesignSpaceMode = DefaultDesignSpaceMode.ATTRIBUTE,
                       include_ingredient_fraction_constraints: bool = False,
                       include_label_fraction_constraints: bool = False,
                       include_label_count_constraints: bool = False,
                       include_parameter_constraints: bool = False) -> DesignSpace:
        """Create a default design space for a predictor.

        This method will return an unregistered design space for all inputs
        that are not responses of the predictor. The design space will contain a
        :class:`~citrine.informatics.design_spaces.formulation_design_space.FormulationDesignSpace`
        for each formulation input. Dimensions are constructed for all other inputs.
        A :class:`~citrine.informatics.dimensions.ContinuousDimension` is constructed for each
        input that corresponds to a :class:`~citrine.informatics.descriptors.RealDescriptor`.
        An :class:`~citrine.informatics.dimensions.EnumeratedDimension` is constructed for all
        other inputs. Enumerated values taken from the allowed ``categories`` of a
        :class:`~citrine.informatics.descriptors.CategoricalDescriptor` or from the
        unique values from the training data for all other descriptors.

        Parameters
        ----------
        predictor_id: UUID
            UUID of the predictor used to construct the design space

        predictor_version: Optional[Union[int, str]]
            Version of the predictor used to construct the design space

        mode: DefaultDesignSpaceMode
            The type of default design space to produce.
            Defaults to DefaultDesignSpaceMode.ATTRIBUTE.

        include_ingredient_fraction_constraints: bool
            Whether to include constraints on ingredient fractions based on the training data.
            Defaults to False.

        include_label_fraction_constraints: bool
            Whether to include constraints on label fractions based on the training data.
            Defaults to False.

        include_label_count_constraints: bool
            Whether to include constraints on labeled ingredient counts based on the training data.
            Defaults to False.

        include_parameter_constraints: bool
            Whether to include constraints on all other inputs based on the training data.
            Defaults to False.

        Returns
        -------
        DesignSpace
            Default design space

        """
        path = f'projects/{self.project_id}/design-spaces/default'
        settings = DesignSpaceSettings(
            predictor_id=predictor_id,
            predictor_version=predictor_version,
            mode=mode,
            include_ingredient_fraction_constraints=include_ingredient_fraction_constraints,
            include_label_fraction_constraints=include_label_fraction_constraints,
            include_label_count_constraints=include_label_count_constraints,
            include_parameter_constraints=include_parameter_constraints
        )

        data = self.session.post_resource(path, json=settings.dump(), version=self._api_version)
        ds = self.build(DesignSpace.wrap_instance(data["instance"]))
        ds._settings = settings
        return ds

    def convert_to_hierarchical(
            self,
            uid: Union[UUID, str],
            *,
            predictor_id: Union[UUID, str],
            predictor_version: Optional[Union[int, str]] = None
    ) -> HierarchicalDesignSpace:
        """Convert an existing ProductDesignSpace into an equivalent HierarchicalDesignSpace.

        A :class:`~citrine.informatics.design_spaces.ProductDesignSpace` can be mapped to a
        :class:`~citrine.informatics.design_spaces.HierarchicalDesignSpace` by using the associated
        predictor and its training data to infer the shape of the hierarchical design space.
        Constraints are then transferred from the product design space to the appropriate node
        in the hierarchical design space.

        Parameters
        ----------
        uid: Union[str, UUID]
            UUID of the existing product design space to convert to a hierarchical version
        predictor_id: Union[UUID, str]
            UUID of a predictor associated with the design space.
        predictor_version: Optional[Union[int, str]]
            Version of the predictor to use. Defaults to the most recent version.

        Returns
        -------
        A :class:`~citrine.informatics.design_spaces.HierarchicalDesignSpace` modeled on the
        existing :class:`~citrine.informatics.design_spaces.ProductDesignSpace`.

        """
        path = format_escaped_url(
            "projects/{project_id}/design-spaces/{design_space_id}/convert-hierarchical",
            project_id=self.project_id,
            design_space_id=uid
        )
        payload = {
            "predictor_id": str(predictor_id),
        }
        if predictor_version:
            payload["predictor_version"] = predictor_version
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return HierarchicalDesignSpace.build(DesignSpace.wrap_instance(data["instance"]))

    def delete(self, uid: Union[UUID, str]):
        """Design Spaces cannot be deleted at this time."""
        msg = "Design Spaces cannot be deleted at this time. Use 'archive' instead."
        raise NotImplementedError(msg)
