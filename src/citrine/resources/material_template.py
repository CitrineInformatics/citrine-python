"""Resources that represent material templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.storable import Storable
from citrine.resources.property_template import PropertyTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.material_template import MaterialTemplate as TaurusMaterialTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class MaterialTemplate(Storable, Resource['MaterialTemplate'], TaurusMaterialTemplate):
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
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    properties: List[PropertyTemplate] or List[PropertyTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated properties. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this property.

    """

    _response_key = TaurusMaterialTemplate.typ  # 'material_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
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
        DataConcepts.__init__(self, TaurusMaterialTemplate.typ)
        TaurusMaterialTemplate.__init__(self, name=name, properties=properties,
                                        uids=set_default_uid(uids), tags=tags,
                                        description=description)

    @classmethod
    def _build_child_objects(cls, data: dict, data_with_soft_links, session: Session = None):
        """
        Build the property templates and bounds.

        Parameters
        ----------
        data: dict
            A serialized material template.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The serialized material template is modified so that its
             properties are [PropertyTemplate, Bounds].

        """
        if 'properties' in data and len(data['properties']) != 0:
            # Each entry in the list data['properties'] has a property template as the 1st entry
            # and a base bounds as the 2nd entry. They are built in different ways.
            data['properties'] = [[PropertyTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['properties']]

    def __str__(self):
        return '<Material template {!r}>'.format(self.name)


class MaterialTemplateCollection(DataConceptsCollection[MaterialTemplate]):
    """A collection of material templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-templates'
    _individual_key = 'material_template'
    _collection_key = 'material_templates'

    @classmethod
    def get_type(cls) -> Type[MaterialTemplate]:
        """Return the resource type in the collection."""
        return MaterialTemplate
