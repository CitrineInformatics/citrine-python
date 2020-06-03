"""Resources that represent material templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object, SpecifiedMixedList, \
    LinkOrElse
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.object_templates import ObjectTemplateCollection, ObjectTemplate
from citrine.resources.property_template import PropertyTemplate
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.material_template import MaterialTemplate as GEMDMaterialTemplate


class MaterialTemplate(ObjectTemplate, Resource['MaterialTemplate'], GEMDMaterialTemplate):
    """
    A material template.

    Material templates are collections of property templates that constrain the values of
    a material's property attributes, and provide a common structure for describing similar
    materials.

    Parameters
    ----------
    name: str
        The name of the material template.
    description: str, optional
        Long-form description of the material template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    properties: List[PropertyTemplate] or List[PropertyTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated properties. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this property.

    """

    _response_key = GEMDMaterialTemplate.typ  # 'material_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        SpecifiedMixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 properties: Optional[Sequence[Union[PropertyTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[PropertyTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        # properties is a list, each element of which is a PropertyTemplate OR is a list with
        # 2 entries: [PropertyTemplate, BaseBounds]. Python typing is not expressive enough, so
        # the typing above is more general.
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDMaterialTemplate.typ)
        GEMDMaterialTemplate.__init__(self, name=name, properties=properties,
                                      uids=uids, tags=tags,
                                      description=description)

    def __str__(self):
        return '<Material template {!r}>'.format(self.name)


class MaterialTemplateCollection(ObjectTemplateCollection[MaterialTemplate]):
    """A collection of material templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-templates'
    _individual_key = 'material_template'
    _collection_key = 'material_templates'

    @classmethod
    def get_type(cls) -> Type[MaterialTemplate]:
        """Return the resource type in the collection."""
        return MaterialTemplate
