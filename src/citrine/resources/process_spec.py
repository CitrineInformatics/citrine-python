"""Resources that represent process spec objects."""
from typing import Optional, Dict, List, Type

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
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec
from taurus.entity.template.process_template import ProcessTemplate as TaurusProcessTemplate


class ProcessSpec(Storable, Resource['ProcessSpec'], TaurusProcessSpec):
    """
    A process specification.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
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

    _response_key = TaurusProcessSpec.typ  # 'process_spec'

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
                 template: Optional[TaurusProcessTemplate] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusProcessSpec.typ)
        TaurusProcessSpec.__init__(self, name=name, uids=set_default_uid(uids),
                                   tags=tags, conditions=conditions, parameters=parameters,
                                   template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process spec {!r}>'.format(self.name)

    @classmethod
    def _build_discarded_objects(cls, obj, obj_with_soft_links, session: Session = None):
        """
        Build the IngredientSpec objects that this ProcessSpec has soft links to.

        The ingredient specs are found in `obj_with_soft_link`

        This method modifies the object in place.

        Parameters
        ----------
        obj: ProcessSpec
            A ProcessSpec object that might be missing some links to IngredientSpec objects.
        obj_with_soft_links: dict or \
        :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            A representation of the ProcessSpec in which the IngredientSpecs are encoded.
            We consider both the possibility that this is a dictionary with an 'ingredients' key
            and that it is a
            :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            (presumably a
            :py:class:`TaurusProcessSpec <taurus.entity.process_spec.ProcessSpec>`)
            with a .ingredients field.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The ProcessSpec object is modified so that it has links to its IngredientSpecs.

        """
        from citrine.resources.ingredient_spec import IngredientSpec
        DataConcepts._build_list_of_soft_links(
            obj, obj_with_soft_links, field='ingredients', reverse_field='process',
            linked_type=IngredientSpec, session=session)


class ProcessSpecCollection(DataConceptsCollection[ProcessSpec]):
    """Represents the collection of all process specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-specs'
    _individual_key = 'process_spec'
    _collection_key = 'process_specs'

    @classmethod
    def get_type(cls) -> Type[ProcessSpec]:
        """Return the resource type in the collection."""
        return ProcessSpec
