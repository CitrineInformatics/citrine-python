from typing import Optional, Set, Union
from uuid import UUID

from gemd import LinkByUID

from citrine._rest.ai_resource_metadata import AIResourceMetadata
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.resources.project import Project
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.informatics.dimensions import Dimension
from citrine.informatics.design_spaces import FormulationDesignSpace
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = [
    "TemplateLink",
    "MaterialNodeDefinition",
    "MaterialHistoryDesignSpace"
]


class TemplateLink(Serializable["TemplateLink"]):
    """Link to a Citrine Platform material and process template for a material node definition.

    Parameters
    ----------
    project: Project
        Project containing the material and process templates,
        used to resolve Citrine Platform UUIDs.
    material_template: Union[UUID, str, LinkByUid, MaterialTemplate]
        Citrine ID referencing an on-platform material template.
    process_template: Union[UUID, str, LinkByUid, ProcessTemplate]
        Citrine ID referencing an on-platform process template.
    """

    material_template = properties.UUID("material_template")
    process_template = properties.UUID("process_template")

    _name = properties.String("name")
    """Simple name used to refer to the combination of material and process template."""

    MaterialTemplateType = Union[UUID, str, LinkByUID, MaterialTemplate]
    ProcessTemplateType = Union[UUID, str, LinkByUID, ProcessTemplate]

    def __init__(
            self,
            project: Project,
            *,
            material_template: MaterialTemplateType,
            process_template: ProcessTemplateType
    ):
        resolved_mat = project.gemd.get(material_template)
        resolved_proc = project.gemd.get(process_template)

        self.material_template = resolved_mat.uids["id"]
        self.process_template = resolved_proc.uids["id"]
        self._name = f"{resolved_proc.name}-{resolved_mat.name}"


class MaterialNodeDefinition(Serializable["MaterialNodeDefinition"]):
    """A single node in a material history design space.

    Parameters
    ----------
    name: str
        A unique name used to reference the materials produced by this node in the design space.
        This name should be used to identify the material when used as an ingredient
        in the formulation subspace of a different node.
    scope: Optional[str]
        An optional custom scope used to identify the materials produced by this node.
    attributes: Set[Dimension]
        Set of dimensions included on materials produced by this node.
    formulation_subspace: Optional[FormulationDesignSpace]
        An optional formulation design space defining the ingredients, labels,
        and constraints for formulations in materials produced by this node.
    template_link: Optional[TemplateLink]
        A set of identifiers linking the materials produced by this node to
        material and process templates on the Citrine Platform.

    """

    name = properties.String("identifier.id")
    scope = properties.Optional(properties.String, "identifier.scope")
    attributes = properties.Set(properties.Object(Dimension), "attributes")
    formulation_subspace = properties.Optional(
        properties.Object(FormulationDesignSpace), "formulation"
    )
    template_link = properties.Optional(properties.Object(TemplateLink), "template")

    def __init__(
            self,
            *,
            name: str,
            scope: Optional[str] = None,
            attributes: Optional[Set[Dimension]] = None,
            formulation_subspace: Optional[FormulationDesignSpace] = None,
            template_link: Optional[TemplateLink] = None
    ):
        self.name = name
        self.scope = scope
        self.attributes = attributes or set()
        self.formulation_subspace = formulation_subspace
        self.template_link = template_link

    @property
    def template_name(self) -> Optional[str]:
        return self.template_link.name if self.template_link else None

    @property
    def material_template(self) -> Optional[UUID]:
        return self.template_link.material_template if self.template_link else None

    @property
    def process_template(self) -> Optional[UUID]:
        return self.template_link.process_template if self.template_link else None

    def __repr__(self):
        return "<MaterialNodeDefinition {!r}>".format(self.name)


class MaterialHistoryDesignSpace(
    Resource["MaterialHistoryDesignSpace"], DesignSpace, AIResourceMetadata
):
    """A design space that produces material history candidates.

    A material history design space always contains a root node that defines the
    attributes and formulation contents included on terminal materials of the candidates.
    It also includes a set of sub-nodes that can be used to define the any new
    intermediate mixtures that appear in the history of the terminal material.

    Material histories produced by this design space are connected based on the
    name identifiers and formulation contents of each node.
    For example, the root node may contain a formulation subspace with an ingredient named
    'New Mixture-001'. If this ingredient matches the `name` field on one of the sub-nodes
    in the design space, the resulting candidates will contain a terminal material with this
    new mixture as one of its ingredients. This procedure can be extended to sub-nodes
    referencing other sub-nodes, allowing for the linkage of complex material history shapes
    in the resulting candidates.

    Every node in the design space also contains a set of `Dimension`s used to define any
    attributes (i.e., properties, processing parameters) that should appear on new materials
    produced by that node.

    Parameters
    ----------
    name: str
        the name of the design space
    description: str
        the description of the design space
    root: MaterialNodeDefinition
        the terminal material node produced by the design space
    subspaces: Set[MaterialNodeDefinition]
        the sub material nodes produced by the design space

    """

    _resource_type = ResourceTypeEnum.MODULE

    root = properties.Object(MaterialNodeDefinition, "config.root")
    subspaces = properties.Set(
        properties.Object(MaterialNodeDefinition), "config.subspaces", default=set()
    )

    status = properties.String("status", serializable=False)
    module_type = properties.String("module_type", default="DESIGN_SPACE")
    typ = properties.String(
        "config.type", default="MaterialHistoryDesignSpace", deserializable=False
    )

    def __init__(
            self,
            name: str,
            *,
            description: str,
            root: MaterialNodeDefinition,
            subspaces: Optional[Set[MaterialNodeDefinition]] = None
    ):
        self.name: str = name
        self.description: str = description
        self.root: MaterialNodeDefinition = root
        self.subspaces: Set[MaterialNodeDefinition] = subspaces or set()

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        data["config"]["root"] = cls.__build_format(data["config"]["root"])
        data["config"]["subspaces"] = {
            cls.__build_format(node) for node in data["config"]["subspaces"]
        }
        return data

    @staticmethod
    def __build_format(node: dict) -> dict:
        # Wrap formulation in a "config" block so it can be deserialized as FormulationDesignSpace
        formulation = node.pop("formulation")
        if formulation:
            node["formulation"] = {"config": formulation}
        return node

    def _post_dump(self, data: dict) -> dict:
        data["config"]["root"] = self.__dump_format(data["config"]["root"])
        data["config"]["subspaces"] = {
            self.__dump_format(x) for x in data["config"]["subspaces"]
        }
        return data

    @staticmethod
    def __dump_format(node: dict) -> dict:
        formulation = node.pop("formulation")
        if formulation:
            node["formulation"] = formulation["config"]
        return node

    def __repr__(self):
        return "<MaterialHistoryDesignSpace {!r}>".format(self.name)
