"""Resources that represent parameter templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object
from citrine._utils.functions import set_default_uid
from citrine.resources.attribute_templates import AttributeTemplate, AttributeTemplateCollection
from citrine.resources.data_concepts import DataConcepts
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.template.parameter_template import ParameterTemplate as TaurusParameterTemplate


class ParameterTemplate(AttributeTemplate, Resource['ParameterTemplate'], TaurusParameterTemplate):
    """
    A parameter template.

    Parameters
    ----------
    name: str
        The name of the parameter template.
    bounds: :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`
        Bounds circumscribe the values that are valid according to this parameter template.
    description: str, optional
        A long-form description of the parameter template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.

    """

    _response_key = TaurusParameterTemplate.typ  # 'parameter_template'

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
        DataConcepts.__init__(self, TaurusParameterTemplate.typ)
        TaurusParameterTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                         uids=set_default_uid(uids), description=description)

    def __str__(self):
        return '<Parameter template {!r}>'.format(self.name)


class ParameterTemplateCollection(AttributeTemplateCollection[ParameterTemplate]):
    """A collection of parameter templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/parameter-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/parameter-templates'
    _individual_key = 'parameter_template'
    _collection_key = 'parameter_templates'

    @classmethod
    def get_type(cls) -> Type[ParameterTemplate]:
        """Return the resource type in the collection."""
        return ParameterTemplate
