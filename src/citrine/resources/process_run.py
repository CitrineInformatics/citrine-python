"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.dict_serializable import DictSerializable
from taurus.entity.file_link import FileLink
from taurus.entity.link_by_uid import LinkByUID
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

    @classmethod
    def _build_soft_linked_objects(cls, obj, obj_with_soft_links, session: Session = None):
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
        ingredients = None
        # Get the ingredients list, if it exists.
        if isinstance(obj_with_soft_links, dict):
            if obj_with_soft_links.get('ingredients'):
                ingredients = obj_with_soft_links['ingredients']
        if isinstance(obj_with_soft_links, DictSerializable):
            if hasattr(obj_with_soft_links, 'ingredients'):
                ingredients = getattr(obj_with_soft_links, 'ingredients')
        if ingredients is None:
            return

        from citrine.resources.ingredient_run import IngredientRun
        for ingredient in ingredients:
            # Cycle through ingredients and if they are not LinkByUID, build them and then
            # set their `process` field to obj
            assert isinstance(ingredient, DictSerializable)
            if isinstance(ingredient, LinkByUID):
                pass
            setattr(ingredient, 'process', None)
            ingredient_object = IngredientRun.build(ingredient, session)
            setattr(ingredient_object, 'process', obj)
        return


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
