from typing import Optional, Sequence, Set
from uuid import UUID

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.design_spaces import FormulationDesignSpace
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine._rest.ai_resource_metadata import AIResourceMetadata

from citrine.informatics.dimensions import Dimension

__all__ = [
    "TemplateLink",
    "MaterialNodeDefinition",
    "MaterialHistoryDesignSpace"
]
    

class TemplateLink(Serializable["TemplateLink"]):
    """Link to a set of material/process templates for a material node definition.

    Parameters
    ----------
    material_template: UUID
        Citrine ID referencing an on-platform material template.
    process_template: UUID
        Citrine ID referencing an on-platform process template.
    name: str
        A custom name used to refer to the combination of material/process templates.
        (Default: "")
    """

    name = properties.String("name")
    material_template = properties.UUID("material_template")
    process_template = properties.UUID("process_template")

    def __init__(
            self,
            *,
            material_template: UUID,
            process_template: UUID,
            name: str = "",
    ):
        self.name = name
        self.material_template = material_template
        self.process_template = process_template


class MaterialNodeDefinition(Serializable["MaterialNodeDefinition"]):
    """A single node in a material history design space.

    Parameters
    ----------
    name: str
        A unique name used to reference the materials produced by this node in the design space.
        If the material produced by this node is used as an ingredient in other node definitions,
        this name should appear as an ingredient name in the other node's formulation subspace.
    scope: Optional[str]
        An optional custom scope used to identify materials produced by this design space.
    attributes: Set[Dimension]
        Set of dimensions included on materials produced by this node.
    formulation_subspace: Optional[FormulationDesignSpace]
        An optional formulation design space defining the ingredients, labels,
        and constraints for formulations produced by this node.
    template_link: Optional[TemplateLink]
        A set of identifiers linking materials produced by this node to Citrine Platform
        material and process templates.

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

    A material history design space begins with a root node that defines the
    attributes and formulations included on the terminal materials of the resulting histories.
    It also includes a set of sub-nodes that can be used to define the structure of any new
    intermediate mixtures that appear in the history of the root node.

    The process structure of the material history candidates is defined through the `name`
    and `formulation_subspace` fields of the material node definitions.


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
