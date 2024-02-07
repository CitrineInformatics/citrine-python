from typing import Optional, List
from uuid import UUID

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.data_sources import DataSource
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
    material_template_name: Optional[str]
        Optional name of the material template.
    process_template_name: Optional[str]
        Optional name of the process template.

    """

    material_template = properties.UUID("material_template")
    process_template = properties.UUID("process_template")
    material_template_name = properties.Optional(properties.String, "material_template_name")
    process_template_name = properties.Optional(properties.String, "process_template_name")

    def __init__(
            self,
            *,
            material_template: UUID,
            process_template: UUID,
            material_template_name: Optional[str] = None,
            process_template_name: Optional[str] = None
    ):
        self.material_template: UUID = material_template
        self.process_template: UUID = process_template
        self.material_template_name: Optional[str] = material_template_name
        self.process_template_name: Optional[str] = process_template_name


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
    display_name: Optional[str]
        Optional name for identifying the node on the Citrine Platform.
        Solely for display purposes (does not appear in generated hierarchical candidates)

    """

    name = properties.String("identifier.id")
    scope = properties.Optional(properties.String, "identifier.scope")
    attributes = properties.List(properties.Object(Dimension), "attributes")
    formulation_subspace = properties.Optional(
        properties.Object(FormulationDesignSpace), "formulation"
    )
    template_link = properties.Optional(properties.Object(TemplateLink), "template")
    display_name = properties.Optional(properties.String, "display_name")

    def __init__(
            self,
            *,
            name: str,
            scope: Optional[str] = None,
            attributes: Optional[List[Dimension]] = None,
            formulation_subspace: Optional[FormulationDesignSpace] = None,
            template_link: Optional[TemplateLink] = None,
            display_name: Optional[str] = None
    ):
        self.name = name
        self.scope: Optional[str] = scope
        self.attributes = attributes or list()
        self.formulation_subspace: Optional[FormulationDesignSpace] = formulation_subspace
        self.template_link: Optional[TemplateLink] = template_link
        self.display_name: Optional[str] = display_name

    def __repr__(self):
        display_name = self.display_name or self.name
        return f"<MaterialNodeDefinition {display_name}>"


class HierarchicalDesignSpace(EngineResource["HierarchicalDesignSpace"], DesignSpace):
    """A design space that produces hierarchical candidates representing a material history.

    A hierarchical design space always contains a root node that defines the
    attributes and formulation contents included on terminal materials of the candidates.
    It also includes a set of sub-nodes that can be used to define the any new
    materials that appear in the history of the terminal material.

    Material histories produced by this design space are connected based on the
    name identifiers and formulation contents of each node.
    For example, the root node may contain a formulation subspace with an ingredient named
    'New Mixture-001'. If this ingredient matches the `name` field on one of the sub-nodes
    in the design space, the resulting candidates will contain a terminal material with this
    new mixture as one of its ingredients. This procedure can be extended to sub-nodes
    referencing other sub-nodes, allowing for the linkage of complex material history shapes
    in the resulting candidates.

    Every node also contains a set of :class:`~citrine.informatics.dimensions.Dimension`\\s
    used to define any attributes (i.e., properties, processing parameters)
    that will appear on the materials produced by that node.

    :class:`~citrine.informatics.data_sources.DataSource`\\s can be included on the configuration
    to allow for design over "known" materials. The Citrine Platform will look up
    the ingredient names from formulation subspaces on the design space nodes
    in order to inject their composition/properties into the material history of the candidates.
    When constructing a default hierarchical design space,
    the Citrine Platform includes any data sources found on the provided predictor configuration.

    Parameters
    ----------
    name: str
        Name of the design space
    description: str
        Description of the design space
    root: MaterialNodeDefinition
        Terminal material node produced by the design space
    subspaces: List[MaterialNodeDefinition]
        Sub material nodes produced by the design space
    data_sources: List[DataSource]
        Data sources used to inject known materials into the hierarchical candidates

    """

    root = properties.Object(MaterialNodeDefinition, "data.instance.root")
    subspaces = properties.List(
        properties.Object(MaterialNodeDefinition), "data.instance.subspaces"
    )
    data_sources = properties.List(
        properties.Object(DataSource), "data.instance.data_sources"
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
            subspaces: Optional[List[MaterialNodeDefinition]] = None,
            data_sources: Optional[List[DataSource]] = None
    ):
        self.name: str = name
        self.description: str = description
        self.root: MaterialNodeDefinition = root
        self.subspaces: List[MaterialNodeDefinition] = subspaces or list()
        self.data_sources: List[DataSource] = data_sources or list()

    def _post_dump(self, data: dict) -> dict:
        data = super()._post_dump(data)

        root_node = data["instance"]["root"]
        data["instance"]["root"] = self.__unwrap_node(root_node)

        data["instance"]["subspaces"] = [
            self.__unwrap_node(sub_node)
            for sub_node in data['instance']['subspaces']
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
    def __wrap_node(node_data: dict) -> dict:
        formulation_subspace = node_data.pop('formulation', None)
        if formulation_subspace:
            node_data['formulation'] = DesignSpace.wrap_instance(formulation_subspace)
        return node_data

    @staticmethod
    def __unwrap_node(node_data: dict) -> dict:
        formulation_subspace = node_data.pop('formulation', None)
        if formulation_subspace:
            node_data['formulation'] = formulation_subspace['data']['instance']
            node_data['formulation']['name'] = formulation_subspace['data']['name']
            node_data['formulation']['description'] = formulation_subspace['data']['description']
        return node_data

    def __repr__(self):
        return f'<HierarchicalDesignSpace {self.name}>'
