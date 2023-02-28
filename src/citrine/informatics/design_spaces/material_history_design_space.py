from typing import List, Optional
from copy import deepcopy

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine.informatics.design_spaces import FormulationDesignSpace
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine._rest.ai_resource_metadata import AIResourceMetadata

from citrine.informatics.dimensions import Dimension

__all__ = [
    'MaterialNodeDefinition',
    'MaterialHistoryDesignSpace'
]


class CustomIdentifier(Resource['CustomIdentifier']):

    identifier = properties.String("id")
    scope = properties.Optional(properties.String, "scope")

    def __init__(self):
        pass  # pragma: no cover


class TemplateIdentifier(Resource['TemplateIdentifier']):
    """A node identifier that links to a GEMD material and process template."""

    template_name = properties.String("templateName")
    material_template = properties.UUID("materialTemplate")
    process_template = properties.UUID("processTemplate")

    def __init__(self):
        pass  # pragma: no cover


class MaterialNodeDefinition(Resource['MaterialNodeDefinition']):
    """A single node in a MaterialHistoryDesignSpace."""

    identifier = properties.Object(CustomIdentifier, "identifier")
    attributes = properties.Set(properties.Object(Dimension), "attributes")
    formulation = properties.Optional(properties.Object(FormulationDesignSpace), "formulation")
    template = properties.Optional(properties.Object(TemplateIdentifier), "template")

    def __init__(self):
        pass  # pragma: no cover

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        print(data)
        if "formulation" in data:
            data["formulation"] = {"config": data["formulation"]}
        return data


class MaterialHistoryDesignSpace(Resource['ProductDesignSpace'], DesignSpace, AIResourceMetadata):
    """A design space that can produce candidates as material histories.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    root: MaterialNodeDefinition
        the root node of the material history candidates
    subspaces: List[MaterialNodeDefinition]
        the list of subspaces to combine, containing dimensions and optional formulation spaces

    """

    _resource_type = ResourceTypeEnum.MODULE

    root = properties.Object(MaterialNodeDefinition, 'config.root')
    subspaces = properties.List(
        properties.Object(MaterialNodeDefinition), 'config.subspaces', default=[]
    )

    # Product design spaces should not be embedded in other subspaces, hence status is required
    status = properties.String('status', serializable=False)

    typ = properties.String(
        'config.type', default='MaterialHistoryDesignSpace', deserializable=False
    )
    module_type = properties.String('module_type', default='DESIGN_SPACE')

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
        self.subspaces: List[MaterialNodeDefinition] = subspaces or []

    def dump(self) -> dict:
        """Override dump to replace on-platform subspaces with their uids."""
        model_copy = deepcopy(self)
        for i, subspace in enumerate(model_copy.subspaces):
            if isinstance(subspace, DesignSpace) and subspace.uid is not None:
                model_copy.subspaces[i] = subspace.uid
        serialized = properties.Object(ProductDesignSpace).serialize(model_copy)
        return self._post_dump(serialized)

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        for i, subspace in enumerate(data['config']['subspaces']):
            if isinstance(subspace, dict):
                # embedded design spaces are not modules, so only serialize their config
                data['config']['subspaces'][i] = subspace['config']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        subspaces = data['config'].get('subspaces', [])
        # For each subspace, rename the `instance` key to `config`.
        for i, _ in enumerate(subspaces):
            data['config']['subspaces'][i]['config'] = \
                data['config']['subspaces'][i].pop('instance')
        return data

    def __str__(self):
        return '<MaterialHistoryDesignSpace {!r}>'.format(self.name)
