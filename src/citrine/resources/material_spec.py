"""Resources that represent material spec data objects."""
from logging import getLogger
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

import deprecation

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, LinkOrElse, Mapping, Object
from citrine.resources.data_concepts import DataConcepts, CITRINE_SCOPE
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.attribute.property_and_conditions import PropertyAndConditions
from gemd.entity.file_link import FileLink
from gemd.entity.object.material_spec import MaterialSpec as GEMDMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.template.material_template import MaterialTemplate as GEMDMaterialTemplate

logger = getLogger(__name__)


class MaterialSpec(ObjectSpec, Resource['MaterialSpec'], GEMDMaterialSpec):
    """
    A material specification.

    Parameters
    ----------
    name: str
        Name of the material spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the material spec.
    process: ProcessSpec
        Process that produces this material.
    properties: List[PropertyAndConditions], optional
        Properties of the material, along with an optional list of conditions under which
        those properties are measured.
    template: MaterialTemplate, optional
        A template bounding the valid values for this material's properties.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDMaterialSpec.typ  # 'material_spec'

    name = String('name', override=True)
    uids = Mapping(String('scope'), String('id'), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)
    notes = PropertyOptional(String(), 'notes', override=True)
    process = PropertyOptional(LinkOrElse(), 'process', override=True)
    properties = PropertyOptional(
        PropertyList(Object(PropertyAndConditions)), 'properties', override=True)
    template = PropertyOptional(LinkOrElse(), 'template', override=True)
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links', override=True)
    typ = String('type')

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 process: Optional[GEMDProcessSpec] = None,
                 properties: Optional[List[PropertyAndConditions]] = None,
                 template: Optional[GEMDMaterialTemplate] = None,
                 file_links: Optional[List[FileLink]] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDMaterialSpec.typ)
        GEMDMaterialSpec.__init__(self, name=name, uids=uids,
                                  tags=tags, process=process, properties=properties,
                                  template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material spec {!r}>'.format(self.name)


class MaterialSpecCollection(ObjectSpecCollection[MaterialSpec]):
    """Represents the collection of all material specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-specs'
    _individual_key = 'material_spec'
    _collection_key = 'material_specs'
    _resource = MaterialSpec

    @classmethod
    def get_type(cls) -> Type[MaterialSpec]:
        """Return the resource type in the collection."""
        return MaterialSpec

    @deprecation.deprecated(details='Use list_by_template instead.')
    def filter_by_template(self,
                           template_id: str,
                           template_scope: str = CITRINE_SCOPE,
                           per_page: int = None) -> Iterator[MaterialSpec]:
        """
        [ALPHA] Get all material specs associated with a material template.

        The material template is specified by its scope and id.

        :param template_id: The unique id corresponding to `scope`.
            The lookup will be most efficient if you use the Citrine ID (scope='id')
            of the material template.
        :param template_scope: The scope used to locate the material template.
        :param per_page: The number of results to return per page.
        :return: A search result of material specs
        """
        if per_page is not None:
            logger.warning('The per_page parameter will be ignored. Please remove it.')
        return self.list_by_template(uid=template_id, scope=template_scope)

    def list_by_template(self,
                         uid: Union[UUID, str],
                         scope: str = CITRINE_SCOPE) -> Iterator[MaterialSpec]:
        """
        [ALPHA] Get the material specs using the specified material template.

        Parameters
        ----------
        uid
            The unique ID of the material template whose material spec usages are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[MaterialSpec]
            The material specs using the specified material template.

        """
        return self._get_relation('material-templates', uid=uid, scope=scope)

    def get_by_process(self,
                       uid: Union[UUID, str],
                       scope: str = CITRINE_SCOPE) -> Optional[MaterialSpec]:
        """
        [ALPHA] Get output material of a process.

        Parameters
        ----------
        uid
            The unique ID of the process whose output is to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        MaterialSpec
            The output material of the specified process, or None if no such material exists.

        """
        return next(
            self._get_relation(relation='process-specs', uid=uid, scope=scope, per_page=1), None)
