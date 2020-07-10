"""Resources that represent property templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object
from citrine.resources.attribute_templates import AttributeTemplate, AttributeTemplateCollection
from citrine.resources.data_concepts import DataConcepts
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template.property_template import PropertyTemplate as GEMDPropertyTemplate


class PropertyTemplate(AttributeTemplate, Resource['PropertyTemplate'], GEMDPropertyTemplate):
    """
    A property template.

    Parameters
    ----------
    name: str
        The name of the property template.
    bounds: :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`
        Bounds circumscribe the values that are valid according to this property template.
    description: str, optional
        A long-form description of the property template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.

    """

    _response_key = GEMDPropertyTemplate.typ  # 'property_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    bounds = Object(BaseBounds, 'bounds')
    typ = String('type')

    def __init__(self,
                 name: str,
                 bounds: BaseBounds,
                 uids: Optional[Dict[str, str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDPropertyTemplate.typ)
        GEMDPropertyTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                      uids=uids, description=description)

    def __str__(self):
        return '<Property template {!r}>'.format(self.name)


class PropertyTemplateCollection(AttributeTemplateCollection[PropertyTemplate]):
    """A collection of property templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/property-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/property-templates'
    _individual_key = 'property_template'
    _collection_key = 'property_templates'
    _resource = PropertyTemplate

    @classmethod
    def get_type(cls) -> Type[PropertyTemplate]:
        """Return the resource type in the collection."""
        return PropertyTemplate
