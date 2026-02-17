"""Resources that represent collections of design spaces."""
from collections.abc import Iterable
from functools import partial
from typing import Optional
from uuid import UUID


from citrine._utils.functions import format_escaped_url
from citrine.informatics.design_spaces import DefaultDesignSpaceMode, DesignSpaceSettings, \
    HierarchicalDesignSpace, TopLevelDesignSpace
from citrine._rest.collection import Collection
from citrine._session import Session


class DesignSpaceCollection(Collection[TopLevelDesignSpace]):
    """Represents the collection of design spaces as well as the resources belonging to it.

    Parameters
    ----------
    project_id: UUID
        the UUID of the project

    """

    _api_version = 'v3'
    _path_template = '/projects/{project_id}/design-spaces'
    _individual_key = None
    _resource = TopLevelDesignSpace
    _collection_key = 'response'
    _enumerated_cell_limit = 128 * 2000

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def build(self, data: dict) -> TopLevelDesignSpace:
        """Build an individual design space."""
        design_space: TopLevelDesignSpace = TopLevelDesignSpace.build(data)
        design_space._session = self.session
        design_space._project_id = self.project_id
        return design_space

    def register(self, design_space: TopLevelDesignSpace) -> TopLevelDesignSpace:
        """Create a new design space."""
        registered_ds = super().register(design_space)

        # If the initial response is invalid, just return it.
        # If not, kick off validation, since we never exposed saving a design space without
        # validation so we should continue to do it automatically
        if registered_ds.failed():
            return registered_ds
        else:
            return self._validate(registered_ds.uid)

    def update(self, design_space: TopLevelDesignSpace) -> TopLevelDesignSpace:
        """Update and validate an existing DesignSpace."""
        updated_ds = super().update(design_space)

        # If the initial response is invalid, just return it.
        # If not, kick off validation, since we never exposed saving a design space without
        # validation so we should continue to do it automatically
        if updated_ds.failed():
            return updated_ds
        else:
            return self._validate(updated_ds.uid)

    def _validate(self, uid: UUID | str) -> TopLevelDesignSpace:
        path = self._get_path(uid, action="validate")
        entity = self.session.put_resource(path, {}, version=self._api_version)
        return self.build(entity)

    def archive(self, uid: UUID | str) -> TopLevelDesignSpace:
        """Archiving a design space removes it from view, but is not a hard delete.

        Parameters
        ----------
        uid: UUID | str
            Unique identifier of the design space to archive

        """
        url = self._get_path(uid, action="archive")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def restore(self, uid: UUID | str) -> TopLevelDesignSpace:
        """Restore an archived design space.

        Parameters
        ----------
        uid: UUID | str
            Unique identifier of the design space to restore

        """
        url = self._get_path(uid, action="restore")
        entity = self.session.put_resource(url, {}, version=self._api_version)
        return self.build(entity)

    def _list_base(self, *, per_page: int = 100, archived: Optional[bool] = None):
        filters = {}
        if archived is not None:
            filters["archived"] = archived

        fetcher = partial(self._fetch_page, additional_params=filters, version="v4")
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list_all(self, *, per_page: int = 20) -> Iterable[TopLevelDesignSpace]:
        """List all design spaces."""
        return self._list_base(per_page=per_page)

    def list(self, *, per_page: int = 20) -> Iterable[TopLevelDesignSpace]:
        """List non-archived design spaces."""
        return self._list_base(per_page=per_page, archived=False)

    def list_archived(self, *, per_page: int = 20) -> Iterable[TopLevelDesignSpace]:
        """List archived design spaces."""
        return self._list_base(per_page=per_page, archived=True)

    def create_default(self,
                       *,
                       predictor_id: UUID | str,
                       predictor_version: Optional[int | str] = None,
                       mode: DefaultDesignSpaceMode = DefaultDesignSpaceMode.ATTRIBUTE,
                       include_ingredient_fraction_constraints: bool = False,
                       include_label_fraction_constraints: bool = False,
                       include_label_count_constraints: bool = False,
                       include_parameter_constraints: bool = False) -> TopLevelDesignSpace:
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

        predictor_version: Optional[int | str]
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
        TopLevelDesignSpace
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
        ds = self.build(TopLevelDesignSpace.wrap_instance(data["instance"]))
        ds._settings = settings
        return ds

    def convert_to_hierarchical(
            self,
            uid: UUID | str,
            *,
            predictor_id: UUID | str,
            predictor_version: Optional[int | str] = None
    ) -> HierarchicalDesignSpace:
        """Convert an existing ProductDesignSpace into an equivalent HierarchicalDesignSpace.

        A :class:`~citrine.informatics.design_spaces.ProductDesignSpace` can be mapped to a
        :class:`~citrine.informatics.design_spaces.HierarchicalDesignSpace` by using the associated
        predictor and its training data to infer the shape of the hierarchical design space.
        Constraints are then transferred from the product design space to the appropriate node
        in the hierarchical design space.

        Parameters
        ----------
        uid: str | UUID
            UUID of the existing product design space to convert to a hierarchical version
        predictor_id: UUID | str
            UUID of a predictor associated with the design space.
        predictor_version: Optional[int | str]
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
        return HierarchicalDesignSpace.build(TopLevelDesignSpace.wrap_instance(data["instance"]))

    def delete(self, uid: UUID | str):
        """Design Spaces cannot be deleted at this time."""
        msg = "Design Spaces cannot be deleted at this time. Use 'archive' instead."
        raise NotImplementedError(msg)
