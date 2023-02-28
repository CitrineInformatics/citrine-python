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
        the name of the design space
    scope: str

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
            attributes: Optional[Sequence[Dimension]] = None,
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
    """A design space that produces candidates as material histories.

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
        data["config"]["root"] = cls.__build_format_node(data["config"]["root"])
        data["config"]["subspaces"] = {
            cls.__build_format_node(node) for node in data["config"]["subspaces"]
        }
        return data

    @staticmethod
    def __build_format_node(node: dict) -> dict:
        # Wrap formulation in a "config" block so it can be deserialized as FormulationDesignSpace
        formulation_data = node.pop("formulation")
        if formulation_data:
            node["formulation"] = {"config": formulation_data}
        return node

    def _post_dump(self, data: dict) -> dict:
        data["config"]["root"] = self.__dump_format_node(data["config"]["root"])
        data["config"]["subspaces"] = {
            self.__dump_format_node(x) for x in data["config"]["subspaces"]
        }
        return data

    @staticmethod
    def __dump_format_node(node: dict) -> dict:
        formulation = node.pop("formulation")
        if formulation:
            node["formulation"] = formulation["config"]
        return node

    def __repr__(self):
        return "<MaterialHistoryDesignSpace {!r}>".format(self.name)
