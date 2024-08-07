"""Resources that represent parameter templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import GEMDResource
from citrine.resources.attribute_templates import AttributeTemplate, AttributeTemplateCollection
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template.parameter_template import ParameterTemplate as GEMDParameterTemplate


class ParameterTemplate(
    GEMDResource['ParameterTemplate'],
    AttributeTemplate,
    GEMDParameterTemplate,
    typ=GEMDParameterTemplate.typ
):
    """
    A parameter template.

    Parameters
    ----------
    name: str
        The name of the parameter template.
    bounds: :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`
        Bounds circumscribe the values that are valid according to this parameter template.
    description: str, optional
        A long-form description of the parameter template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.

    """

    _response_key = GEMDParameterTemplate.typ  # 'parameter_template'

    def __init__(self,
                 name: str,
                 *,
                 bounds: BaseBounds,
                 uids: Optional[Dict[str, str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        if uids is None:
            uids = dict()
        super(AttributeTemplate, self).__init__()
        GEMDParameterTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                       uids=uids, description=description)

    def __str__(self):
        return '<Parameter template {!r}>'.format(self.name)


class ParameterTemplateCollection(AttributeTemplateCollection[ParameterTemplate]):
    """A collection of parameter templates."""

    _individual_key = 'parameter_template'
    _collection_key = 'parameter_templates'
    _resource = ParameterTemplate

    @classmethod
    def get_type(cls) -> Type[ParameterTemplate]:
        """Return the resource type in the collection."""
        return ParameterTemplate
