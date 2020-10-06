"""Resources that represent condition templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object
from citrine.resources.attribute_templates import AttributeTemplate, AttributeTemplateCollection
from citrine.resources.data_concepts import DataConcepts
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template.condition_template import ConditionTemplate as GEMDConditionTemplate


class ConditionTemplate(AttributeTemplate, Resource['ConditionTemplate'], GEMDConditionTemplate):
    """
    A condition template.

    Parameters
    ----------
    name: str
        The name of the condition template.
    bounds: :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`
        Bounds circumscribe the values that are valid according to this condition template.
    description: str, optional
        A long-form description of the condition template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.

    """

    _response_key = GEMDConditionTemplate.typ  # 'condition_template'

    name = String('name', override=True)
    description = PropertyOptional(String(), 'description', override=True)
    uids = Mapping(String('scope'), String('id'), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)
    bounds = Object(BaseBounds, 'bounds', override=True)
    typ = String('type')

    def __init__(self,
                 name: str,
                 *,
                 bounds: BaseBounds,
                 uids: Optional[Dict[str, str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None
                 ):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDConditionTemplate.typ)
        GEMDConditionTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                       uids=uids, description=description)

    def __str__(self):
        return '<Condition template {!r}>'.format(self.name)


class ConditionTemplateCollection(AttributeTemplateCollection[ConditionTemplate]):
    """A collection of condition templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/condition-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/condition-templates'
    _individual_key = 'condition_template'
    _collection_key = 'condition_templates'
    _resource = ConditionTemplate

    @classmethod
    def get_type(cls) -> Type[ConditionTemplate]:
        """Return the resource type in the collection."""
        return ConditionTemplate
