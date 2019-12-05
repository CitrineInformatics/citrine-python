"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.storable import Storable
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.file_link import FileLink
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec
from taurus.entity.source.performed_source import PerformedSource


class ProcessRun(Storable, Resource['ProcessRun'], TaurusProcessRun):
    """
    A process run.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
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

    _response_key = TaurusProcessRun.typ  # 'process_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    source = PropertyOptional(Object(PerformedSource), "source")
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[TaurusProcessSpec] = None,
                 file_links: Optional[List[FileLink]] = None,
                 source: Optional[PerformedSource] = None):
        DataConcepts.__init__(self, TaurusProcessRun.typ)
        TaurusProcessRun.__init__(self, name=name, uids=set_default_uid(uids),
                                  tags=tags, conditions=conditions, parameters=parameters,
                                  spec=spec, file_links=file_links, notes=notes, source=source)

    def __str__(self):
        return '<Process run {!r}>'.format(self.name)

    @classmethod
    def _build_discarded_objects(cls, obj, obj_with_soft_links, session: Session = None):
        """
        Build the IngredientRun objects that this ProcessRun has soft links to.

        The ingredient runs are found in `obj_with_soft_link`

        This method modifies the object in place.

        Parameters
        ----------
        obj: ProcessRun
            A ProcessRun object that might be missing some links to IngredientRun objects.
        obj_with_soft_links: dict or \
        :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            A representation of the ProcessRun in which the IngredientRuns are encoded.
            We consider both the possibility that this is a dictionary with an 'ingredients' key
            and that it is a
            :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            (presumably a
            :py:class:`TaurusProcessRun <taurus.entity.process_run.ProcessRun>`)
            with a .ingredients field.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The ProcessRun object is modified so that it has links to its IngredientRuns.

        """
        from citrine.resources.ingredient_run import IngredientRun
        DataConcepts._build_list_of_soft_links(
            obj, obj_with_soft_links, field='ingredients', reverse_field='process',
            linked_type=IngredientRun, session=session)


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
