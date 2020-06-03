"""Resources that represent process spec objects."""
from typing import Optional, Dict, List, Type, Union, Iterator
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.file_link import FileLink
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.template.process_template import ProcessTemplate as GEMDProcessTemplate


class ProcessSpec(ObjectSpec, Resource['ProcessSpec'], GEMDProcessSpec):
    """
    A process specification.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the process spec.
    conditions: List[Condition], optional
        Conditions under which this process spec occurs.
    parameters: List[Parameter], optional
        Parameters of this process spec.
    template: ProcessTemplate, optional
        A template bounding the valid values for this process's parameters and conditions.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    Attributes
    ----------
    output_material: MaterialSpec
        The material spec that this process spec produces. The link is established by creating
        the material spec and settings its `process` field to this process spec.

    ingredients: List[IngredientSpec], optional
        Ingredient specs that act as inputs to this process spec. The link is established by
        creating each ingredient spec and setting its `process` field to this process spec.

    """

    _response_key = GEMDProcessSpec.typ  # 'process_spec'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    template = PropertyOptional(LinkOrElse(), 'template')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 template: Optional[GEMDProcessTemplate] = None,
                 file_links: Optional[List[FileLink]] = None
                 ):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDProcessSpec.typ)
        GEMDProcessSpec.__init__(self, name=name, uids=uids,
                                 tags=tags, conditions=conditions, parameters=parameters,
                                 template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process spec {!r}>'.format(self.name)


class ProcessSpecCollection(ObjectSpecCollection[ProcessSpec]):
    """Represents the collection of all process specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-specs'
    _individual_key = 'process_spec'
    _collection_key = 'process_specs'

    @classmethod
    def get_type(cls) -> Type[ProcessSpec]:
        """Return the resource type in the collection."""
        return ProcessSpec

    def list_by_template(self, uid: Union[UUID, str], scope: str = 'id') -> Iterator[ProcessSpec]:
        """
        [ALPHA] Get the process specs using the specified process template.

        Parameters
        ----------
        uid
            The unique ID of the process template whose process spec usages are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[ProcessSpec]
            The process specs using the specified process template

        """
        return self._get_relation('process-templates', uid=uid, scope=scope)
