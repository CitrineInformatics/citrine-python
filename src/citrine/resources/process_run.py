"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from taurus.entity.file_link import FileLink
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec


class ProcessRun(DataConcepts, Resource['ProcessRun'], TaurusProcessRun):
    """
    A process run.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process run.
    uids: Map[str, str], optional
        A collection of unique identifiers, each a key-value pair. The key is the "scope"
        and the value is the identifier. The scope "id" is reserved for the internal Citrine ID,
        which will always be a uuid4.
    tags: List[str], optional
        A set of tags. Tags can be used for filtering.
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

    Attributes
    ----------
    output_material: MaterialRun
        The material run that this process run produces. The link is established by creating
        the material run and settings its `process` field to this process run.

    ingredients: List[IngredientRun]
        Ingredient runs that act as inputs to this process run. The link is established by
        creating each ingredient run and setting its `process` field to this process run.

    """

    _response_key = TaurusProcessRun.typ  # 'process_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[TaurusProcessSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusProcessRun.typ)
        TaurusProcessRun.__init__(self, name=name, uids=set_default_uid(uids),
                                  tags=tags, conditions=conditions, parameters=parameters,
                                  spec=spec, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process run {!r}>'.format(self.name)


class ProcessRunCollection(DataConceptsCollection[ProcessRun]):
    """Represents the collection of all process runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-runs'
    _individual_key = 'process_run'
    _collection_key = 'process_runs'

    @classmethod
    def get_type(cls) -> Type[ProcessRun]:
        """Return the resource type in the collection."""
        return ProcessRun
