"""Resources that represent collections of design spaces."""
import warnings
from typing import List, Optional, TypeVar, Union
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces import DesignSpace, EnumeratedDesignSpace, \
    HierarchicalDesignSpace, TemplateLink
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

    def _hydrate_design_space(self, design_space: DesignSpace) -> List[DesignSpace]:
        if design_space.typ != "ProductDesignSpace":
            return design_space

        subspaces = []
        for subspace in design_space.subspaces:
            if isinstance(subspace, (str, UUID)):
                warnings.warn("Support for UUIDs in subspaces is deprecated as of 2.16.0, and "
                              "will be dropped in 3.0. Please use DesignSpace objects instead.",
                              DeprecationWarning)
                subspaces.append(self.get(subspace))
            else:
                subspaces.append(subspace)
        design_space.subspaces = subspaces
        return design_space

    def register(self, design_space: DesignSpace) -> DesignSpace:
        """Create a new design space."""
        self._verify_write_request(design_space)
        hydrated_ds = self._hydrate_design_space(design_space)

        registered_ds = super().register(hydrated_ds)

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
        hydrated_ds = self._hydrate_design_space(design_space)
        updated_ds = super().update(hydrated_ds)

        # The /api/v3/design-spaces endpoint switched archiving from a field on the update payload
        # to their own endpoints. To maintain backwards compatibility, all design spaces have an
        # _archived field set by the archived property. It will be archived if True, and restored
        # if False. It defaults to None, which does nothing. The value is reset afterwards.
        if design_space._archived is True:
            self.archive(design_space.uid)
        elif design_space._archived is False:
            self.restore(design_space.uid)
        design_space._archived = None

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
            data_sources: Optional[List[DataSource]] = None,
            template_link: Optional[TemplateLink] = None,
            display_name: Optional[str] = None,
    ) -> HierarchicalDesignSpace:
        """Convert an existing ProductDesignSpace into an equivalent HierarchicalDesignSpace.

        A :class:`~citrine.informatics.design_spaces.ProductDesignSpace` can be mapped to a
        :class:`~citrine.informatics.design_spaces.HierarchicalDesignSpace` with a root node
        containing the dimensions and formulation subspace of the original design space.
        The resulting root node can be supplemented with the data sources, template link,
        and display name provided to this method.

        Data sources enable the Citrine Platform to design over "known" ingredients
        found in the formulation subspace of the original design space.
        These materials are looked up from the data source and injected into the material history
        of the generated candidates.

        Parameters
        ----------
        uid: Union[str, UUID]
            UUID of the existing product design space to convert to a hierarchical version
        data_sources: Optional[List[DataSource]]
            Optional data sources to include in the converted hierarchical design space
        template_link: Optional[TemplateLink]
            Optional template link to include on the root material node
        display_name: Optional[str]
            Optional display name to include on the root material node

        Returns
        -------
        A :class:`~citrine.informatics.design_spaces.HierarchicalDesignSpace`
        with a single material node obtained from the input search space.

        """
        path = f"projects/{self.project_id}/design-spaces/{uid}/convert-hierarchical"
        data_sources = data_sources or []
        payload = {
            "data_sources": [x.dump() for x in data_sources],
            "template_link": template_link.dump() if template_link else None,
            "display_name": display_name
        }
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return HierarchicalDesignSpace.build(DesignSpace.wrap_instance(data["instance"]))

    def delete(self, uid: Union[UUID, str]):
        """Design Spaces cannot be deleted at this time."""
        msg = "Design Spaces cannot be deleted at this time. Use 'archive' instead."
        raise NotImplementedError(msg)
