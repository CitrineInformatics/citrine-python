"""Resources that represent material spec data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, LinkOrElse, Object
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.attribute.property_and_conditions import PropertyAndConditions
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_spec import MaterialSpec as GEMDMaterialSpec
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.template.material_template import MaterialTemplate as GEMDMaterialTemplate


class MaterialSpec(
    GEMDResource['MaterialSpec'],
    ObjectSpec,
    GEMDMaterialSpec,
    typ=GEMDMaterialSpec.typ
):
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

    name = String('name', override=True, use_init=True)
    process = PropertyOptional(LinkOrElse(GEMDProcessSpec),
                               'process',
                               override=True,
                               use_init=True,
                               )
    properties = PropertyOptional(PropertyList(Object(PropertyAndConditions)),
                                  'properties',
                                  override=True)
    template = PropertyOptional(LinkOrElse(GEMDMaterialTemplate),
                                'template',
                                override=True,
                                use_init=True,)

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
        super(ObjectSpec, self).__init__()
        GEMDMaterialSpec.__init__(self, name=name, uids=uids,
                                  tags=tags, process=process, properties=properties,
                                  template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material spec {!r}>'.format(self.name)


class MaterialSpecCollection(ObjectSpecCollection[MaterialSpec]):
    """Represents the collection of all material specs associated with a dataset."""

    _individual_key = 'material_spec'
    _collection_key = 'material_specs'
    _resource = MaterialSpec

    @classmethod
    def get_type(cls) -> Type[MaterialSpec]:
        """Return the resource type in the collection."""
        return MaterialSpec

    def list_by_template(self,
                         uid: Union[UUID, str, LinkByUID, GEMDMaterialTemplate]
                         ) -> Iterator[MaterialSpec]:
        """
        Get the material specs using the specified material template.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMaterialTemplate]
            A representation of the material template whose material spec usages are to be located.

        Returns
        -------
        Iterator[MaterialSpec]
            The material specs using the specified material template.

        """
        return self._get_relation('material-templates', uid=uid)

    def get_by_process(self,
                       uid: Union[UUID, str, LinkByUID, GEMDProcessSpec]
                       ) -> Optional[MaterialSpec]:
        """
        Get output material of a process.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDProcessSpec]
            A representation of the process whose output is to be located.

        Returns
        -------
        MaterialSpec
            The output material of the specified process, or None if no such material exists.

        """
        return next(
            self._get_relation(
                relation='process-specs',
                uid=uid,
                per_page=1
            ),
            None
        )
