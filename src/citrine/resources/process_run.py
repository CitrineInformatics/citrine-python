"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type, Union, Iterator
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine.resources.data_concepts import DataConcepts, _make_link_by_uid
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.process_run import ProcessRun as GEMDProcessRun
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.source.performed_source import PerformedSource


class ProcessRun(ObjectRun, Resource['ProcessRun'], GEMDProcessRun):
    """
    A process run.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the process run.
    conditions: List[Condition], optional
        Conditions under which this process run occurs.
    parameters: List[Parameter], optional
        Parameters of this process run.
    spec: ProcessSpec
        Spec for this process run.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.
    source: PerformedSource, optional
        Information about the person who performed the run and when.

    Attributes
    ----------
    output_material: MaterialRun
        The material run that this process run produces. The link is established by creating
        the material run and settings its `process` field to this process run.

    ingredients: List[IngredientRun]
        Ingredient runs that act as inputs to this process run. The link is established by
        creating each ingredient run and setting its `process` field to this process run.

    """

    _response_key = GEMDProcessRun.typ  # 'process_run'

    name = String('name', override=True)
    uids = Mapping(String('scope'), String('id'), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)
    notes = PropertyOptional(String(), 'notes', override=True)
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions', override=True)
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters', override=True)
    spec = PropertyOptional(LinkOrElse(), 'spec', override=True)
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links', override=True)
    source = PropertyOptional(Object(PerformedSource), "source", override=True)
    typ = String('type')

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[GEMDProcessSpec] = None,
                 file_links: Optional[List[FileLink]] = None,
                 source: Optional[PerformedSource] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDProcessRun.typ)
        GEMDProcessRun.__init__(self, name=name, uids=uids,
                                tags=tags, conditions=conditions, parameters=parameters,
                                spec=spec, file_links=file_links, notes=notes, source=source)

    def __str__(self):
        return '<Process run {!r}>'.format(self.name)


class ProcessRunCollection(ObjectRunCollection[ProcessRun]):
    """Represents the collection of all process runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-runs'
    _individual_key = 'process_run'
    _collection_key = 'process_runs'
    _resource = ProcessRun

    @classmethod
    def get_type(cls) -> Type[ProcessRun]:
        """Return the resource type in the collection."""
        return ProcessRun

    def list_by_spec(self,
                     uid: Union[UUID, str, LinkByUID, GEMDProcessSpec], *,
                     scope: Optional[str] = None) -> Iterator[ProcessRun]:
        """
        [ALPHA] Get the process runs using the specified process spec.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDProcessSpec]
            A representation of the process spec whose process run usages are to be located.
        scope: Optional[str]
           [DEPRECATED] use a LinkByUID to specify a custom scope
            The scope of the uid, defaults to Citrine scope ("id")

        Returns
        -------
        Iterator[ProcessRun]
            The process runs using the specified process spec.

        """
        link = _make_link_by_uid(uid, scope)
        return self._get_relation('process-specs', uid=link.id, scope=link.scope)
