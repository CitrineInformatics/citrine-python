"""Resources that represent collections of design spaces."""
from functools import partial
from typing import Iterable, Optional, TypeVar, Union
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._utils.functions import format_escaped_url
from citrine.informatics.design_spaces import DesignSpace, EnumeratedDesignSpace, \
    HierarchicalDesignSpace
from citrine._rest.collection import Collection
from citrine._session import Session

CreationType = TypeVar('CreationType', bound=DesignSpace)


class DefaultDesignSpaceMode(BaseEnumeration):
    """The type of default design space to create.

    * ATTRIBUTE results in a product design space containing dimensions required by the predictor
    * HIERARCHICAL results in a hierarchical design space resembling the shape of training data
    """

    ATTRIBUTE = 'ATTRIBUTE'
    HIERARCHICAL = 'HIERARCHICAL'


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
        """
        if isinstance(design_space, EnumeratedDesignSpace):
            width = len(design_space.descriptors)
            length = len(design_space.data)
            if width * length > self._enumerated_cell_limit:
                msg = "EnumeratedDesignSpace only supports up to {} descriptor-values, " \
                      "but {} were given. Please reduce the number of descriptors or candidates " \
                      "in this EnumeratedDesignSpace"
                raise ValueError(msg.format(self._enumerated_cell_limit, width * length))

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

    def _list_base(self, *, per_page: int = 100, archived: Optional[bool] = None):
        filters = {}
        if archived is not None:
            filters["archived"] = archived

        fetcher = partial(self._fetch_page,
                          fetch_func=partial(self.session.get_resource, version="v4"),
                          additional_params=filters)
        return self._paginator.paginate(page_fetcher=fetcher,
                                        collection_builder=self._build_collection_elements,
                                        per_page=per_page)

    def list_all(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List the most recent version of all design spaces."""
        return self._list_base(per_page=per_page)

    def list(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List the most recent version of all non-archived design spaces."""
        return self._list_base(per_page=per_page, archived=False)

    def list_archived(self, *, per_page: int = 20) -> Iterable[DesignSpace]:
        """List the most recent version of all archived predictors."""
        return self._list_base(per_page=per_page, archived=True)

    def create_default(self,
                       *,
                       predictor_id: UUID,
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
        payload = {
            "predictor_id": str(predictor_id),
            "mode": mode.value,
            "include_ingredient_fraction_constraints": include_ingredient_fraction_constraints,
            "include_label_fraction_constraints": include_label_fraction_constraints,
            "include_label_count_constraints": include_label_count_constraints,
            "include_parameter_constraints": include_parameter_constraints
        }
        if predictor_version:
            payload["predictor_version"] = predictor_version

        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return self.build(DesignSpace.wrap_instance(data["instance"]))

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
