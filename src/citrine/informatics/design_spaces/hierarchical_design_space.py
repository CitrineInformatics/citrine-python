from typing import Optional, List
from uuid import UUID

from citrine._rest.ai_resource_metadata import AIResourceMetadata
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.dimensions import Dimension
from citrine.informatics.design_spaces import FormulationDesignSpace
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = [
    "TemplateLink",
    "MaterialNodeDefinition",
    "HierarchicalDesignSpace"
]


class TemplateLink(Serializable["TemplateLink"]):
    """Link to a Citrine Platform material and process template for a material node definition.

    Parameters
    ----------
    material_template: UUID
        Citrine ID referencing an on-platform material template.
    process_template: UUID
        Citrine ID referencing an on-platform process template.

    """

    _name = properties.String("name", serializable=False)
    material_template = properties.UUID("material_template")
    process_template = properties.UUID("process_template")

    def __init__(self, *, material_template: UUID, process_template: UUID):
        self.material_template: UUID = material_template
        self.process_template: UUID = process_template


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
    attributes: List[Dimension]
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
    attributes = properties.List(properties.Object(Dimension), "attributes")
    formulation_subspace = properties.Optional(
        properties.Object(FormulationDesignSpace), "formulation"
    )
    template_link = properties.Optional(properties.Object(TemplateLink), "template")

    def __init__(
            self,
            *,
            name: str,
            scope: Optional[str] = None,
            attributes: Optional[List[Dimension]] = None,
            formulation_subspace: Optional[FormulationDesignSpace] = None,
            template_link: Optional[TemplateLink] = None
    ):
        self.name = name
        self.scope: Optional[str] = scope
        self.attributes = attributes or list()
        self.formulation_subspace: Optional[FormulationDesignSpace] = formulation_subspace
        self.template_link: Optional[TemplateLink] = template_link

    def __repr__(self):
        return "<MaterialNodeDefinition {!r}>".format(self.name)


class HierarchicalDesignSpace(
    Resource["HierarchicalDesignSpace"], DesignSpace, AIResourceMetadata
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
    subspaces: List[MaterialNodeDefinition]
        the sub material nodes produced by the design space

    """

    root = properties.Object(MaterialNodeDefinition, "data.instance.root")
    subspaces = properties.List(
        properties.Object(MaterialNodeDefinition), "data.instance.subspaces", default=list()
    )
    typ = properties.String(
        "data.instance.type", default="HierarchicalDesignSpace", deserializable=False
    )

    def __init__(
            self,
            name: str,
            *,
            description: str,
            root: MaterialNodeDefinition,
            subspaces: Optional[List[MaterialNodeDefinition]] = None
    ):
        self.name: str = name
        self.description: str = description
        self.root: MaterialNodeDefinition = root
        self.subspaces: List[MaterialNodeDefinition] = subspaces or list()

    def _post_dump(self, data: dict) -> dict:
        data = super()._post_dump(data)

        root_node = data["data"]["instance"]["root"]
        data["data"]["instance"]["root"] = self.__unwrap_node(root_node)

        data["data"]["instance"]["subspaces"] = [
            self.__unwrap_node(sub_node)
            for sub_node in data['data']['instance']['subspaces']
        ]
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        root_node = data["data"]["instance"]["root"]
        data["data"]["instance"]["root"] = cls.__wrap_node(root_node)

        data["data"]["instance"]["subspaces"] = [
            cls.__wrap_node(sub_node) for sub_node in data['data']['instance']['subspaces']
        ]

        return data

    @staticmethod
    def __wrap_node(node: dict) -> dict:
        formulation_subspace = node.pop('formulation')
        if formulation_subspace:
            node['formulation'] = DesignSpace.wrap_instance(formulation_subspace)
        return node

    @staticmethod
    def __unwrap_node(node: dict) -> dict:
        formulation_subspace = node.pop('formulation')
        if formulation_subspace:
            node['formulation'] = formulation_subspace['data']['instance']
        return node

    def __repr__(self):
        return '<HierarchicalDesignSpace {!r}>'.format(self.name)
