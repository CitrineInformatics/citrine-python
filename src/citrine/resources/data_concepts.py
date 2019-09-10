"""Top-level class for all data concepts objects and collections thereof."""
from uuid import UUID
from typing import TypeVar, Type, List, Dict, Union
from copy import deepcopy
from abc import abstractmethod

from citrine._session import Session
from citrine._rest.collection import Collection
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._serialization.properties import Property, LinkOrElse, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._utils.functions import (
    validate_type, scrub_none,
    replace_objects_with_links, get_object_id)
from taurus.client.json_encoder import loads, dumps, LinkByUID
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.template.attribute_template import AttributeTemplate


class DataConcepts(PolymorphicSerializable['DataConcepts']):
    """
    An abstract data concepts object.

    DataConcepts must be extended along with `Resource`.

    Parameters
    ----------
    typ: str
        A string denoting what type of DataConcepts class a particular instantiation is.

    Attributes
    ----------
    session: Session
        The Citrine session used to connect to the database.

    """

    _local_keys = ['type']
    """list of str: keys that appear in the serialized dictionary but not in the object itself."""

    class_dict = dict()
    """
    Dict[str, class]: dictionary from the type key to the class for every class \
    that extends DataConcepts.

    Only populated if the :func:`get_type` method is invoked.
    """

    def __init__(self, typ: str):
        self.typ = typ
        self.session = None

    @classmethod
    def build(cls, data: dict, session: Session = None):
        """
        Build a data concepts object from a dictionary.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A dictionary representing the serialized object. The dictionary must have a 'type'
            field and its value must correspond to class that is invoking this method.
        session: Session
            the Citrine session to assign to the built object.

        Returns
        -------
        DataConcepts
            An object corresponding to a data concepts resource.

        """
        if 'type' in data and data['type'] == LinkByUID.typ:
            return loads(dumps(data))

        data_copy = deepcopy(data)
        data_copy = validate_type(data_copy, cls._response_key)
        # Running through a taurus loads/dumps cycle validates all of the fields and ensures
        # the object is now in a well-defined format
        data_concepts_dict = loads(dumps(data_copy)).as_dict()
        cls._remove_local_keys(data_concepts_dict)
        cls._build_child_objects(data_concepts_dict)

        data_concepts_object = cls(**data_concepts_dict)
        data_concepts_object.session = session
        return data_concepts_object

    @classmethod
    def _remove_local_keys(cls, data: dict) -> dict:
        """
        Remove each of the 'local' keys in a dictionary.

        Local keys are not meant to be serialized or passed to the class constructor.
        Note that this method modifies the input dictionary.

        Parameters
        ----------
        data: dict
            A dictionary corresponding to a serialized object.

        Returns
        -------
        dict
            The serialized object with local keys removed.

        """
        for key in cls._local_keys:
            if key in data:
                del data[key]
        return data

    @classmethod
    def _build_child_objects(cls, data: dict, session: Session = None) -> dict:
        """
        Build the data concepts objects that this serialized object points to.

        This method modifies the serialized object in place.

        Parameters
        ----------
        data: dict
            A serialized data concepts object.
        session: Session
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The serialized object is modified so that all of its dictionary values that are
            themselves serialized objects have been deserialized .

        """
        def _is_dc(prop_type: Property) -> bool:
            """Determine if a property is a DataConcepts object or LinkByUID."""
            if isinstance(prop_type, LinkOrElse):
                return True
            elif isinstance(prop_type, Object):
                return issubclass(prop_type.klass, DataConcepts)
            elif isinstance(prop_type, PropertyOptional):
                return _is_dc(prop_type.prop)
            elif isinstance(prop_type, PropertyList):
                return _is_dc(prop_type.element_type)
            else:
                return False

        fields = {k: v for k, v in cls.__dict__.items() if isinstance(v, Property)}
        for key, field in fields.items():
            if _is_dc(field):
                if data.get(key):
                    if isinstance(data[key], List):
                        data[key] = [DataConcepts.get_type(elem.as_dict())
                                     .build(elem.as_dict()) for elem in data[key]]
                        for elem in data[key]:
                            if isinstance(elem, DataConcepts):
                                elem.session = session
                    else:
                        data[key] = DataConcepts.get_type(data[key].as_dict()) \
                            .build(data[key].as_dict())
                        if isinstance(data[key], DataConcepts):
                            data[key].session = session

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """
        Determine the class of a serialized object.

        The data dictionary must have a 'type' key whose value corresponds to the response key
        of one of the classes that extends :class:`DataConcepts`.

        Parameters
        ----------
        data: dict
            A dictionary corresponding to a serialized data concepts object of unknown type.

        Returns
        -------
        class
            The class corresponding to data.

        """
        if len(DataConcepts.class_dict) == 0:
            DataConcepts._make_class_dict()
        return DataConcepts.class_dict[data['type']]

    @staticmethod
    def _make_class_dict():
        """Construct a dictionary from each type key to the class."""
        from citrine.attributes.condition import Condition
        from citrine.attributes.parameter import Parameter
        from citrine.attributes.property import Property
        from citrine.attributes.property_and_conditions import PropertyAndConditions
        from citrine.resources.condition_template import ConditionTemplate
        from citrine.resources.parameter_template import ParameterTemplate
        from citrine.resources.property_template import PropertyTemplate
        from citrine.resources.material_template import MaterialTemplate
        from citrine.resources.measurement_template import MeasurementTemplate
        from citrine.resources.process_template import ProcessTemplate
        from citrine.resources.ingredient_spec import IngredientSpec
        from citrine.resources.material_spec import MaterialSpec
        from citrine.resources.measurement_spec import MeasurementSpec
        from citrine.resources.process_spec import ProcessSpec
        from citrine.resources.ingredient_run import IngredientRun
        from citrine.resources.material_run import MaterialRun
        from citrine.resources.measurement_run import MeasurementRun
        from citrine.resources.process_run import ProcessRun
        _clazz_list = [Condition, Parameter, Property, PropertyAndConditions,
                       ConditionTemplate, ParameterTemplate, PropertyTemplate,
                       MaterialTemplate, MeasurementTemplate, ProcessTemplate,
                       IngredientSpec, MaterialSpec, MeasurementSpec, ProcessSpec,
                       IngredientRun, MaterialRun, MeasurementRun, ProcessRun]
        for clazz in _clazz_list:
            DataConcepts.class_dict[clazz._response_key] = clazz
        DataConcepts.class_dict['link_by_uid'] = LinkByUID

    def as_dict(self) -> dict:
        """Dump to a dictionary (useful for interoperability with taurus)."""
        return self.dump()


ResourceType = TypeVar('ResourceType', bound='DataConcepts')


class DataConceptsCollection(Collection[ResourceType]):
    """
    A collection of one kind of data concepts object.

    Parameters
    ----------
    project_id: UUID
        The uid of the project that this collection belongs to.
    dataset_id: UUID
        The uid of the dataset that this collection belongs to. If None then the collection
        ranges over all datasets in the project. Note that this is only allowed for certain
        actions. For example, you can use :func:`filter_by_tags` to search over all datasets,
        but when using :func:`register` to upload or update an object, a dataset must be specified.
    session: Session
        The Citrine session used to connect to the database.

    """

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    @classmethod
    @abstractmethod
    def get_type(cls) -> Type[Serializable]:
        """Return the resource type in the collection."""
        pass

    def build(self, data: dict) -> ResourceType:
        """
        Build an object of type ResourceType from a serialized dictionary.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A serialized data model object.

        Returns
        -------
        DataConcepts
            A data model object built from the dictionary.

        """
        data_concepts_object = self.get_type().build(data)
        data_concepts_object.session = self.session
        return data_concepts_object

    def list(self):
        """
        List all visible elements of the collection.

        Returns
        -------
        List[DataConcepts]
            Every object in this collection.

        """
        return self.filter_by_tags([])

    def register(self, model: ResourceType):
        """
        Create a new element of the collection or update an existing element.

        If the input model has a Citrine ID that corresponds to an existing object in the
        database, then that object will be updated. Otherwise a new object will be created.

        Parameters
        ----------
        model: DataConcepts
            The DataConcepts object.

        Returns
        -------
        DataConcepts
            A copy of the registered object as it now exists in the database.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to register a data model object.")
        path = self._get_path()
        # How do we prepare a citrine-python object to be the json in a POST request?
        # Right now, that method scrubs out None values and replaces top-level objects with links.
        # Eventually, we want to replace it with the following:
        #   dumped_data = dumps(loads(dumps(model.dump())))
        # This dumps the object to a dictionary (model.dump()), and then to a string (dumps()).
        # But this string is still nested--because it's a dictionary, taurus.dumps() does not know
        # how to replace the objects with link-by-uids. loads() converts this string into nested
        # taurus objects, and then the final dumps() converts that to a json-ready string in which
        # all of the object references have been replaced with link-by-uids.
        dumped_data = replace_objects_with_links(scrub_none(model.dump()))
        data = self.session.post_resource(path, dumped_data)
        full_model = self.build(data)
        model.session = self.session
        return full_model

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """
        Get the element of the collection with Citrine ID equal to uid.

        Parameters
        ----------
        uid: Union[UUID, str]
            The Citrine ID.

        Returns
        -------
        DataConcepts
            An object with Citrine ID equal to uid.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to get a data model object.")
        path = self._get_path() + "/id/{}".format(uid)
        data = self.session.get_resource(path)
        return self.build(data)

    def filter_by_tags(self, tags: List[str]):
        """
        Get all objects in the collection that match any one of a list of tags.

        Parameters
        ----------
        tags: List[str]
            a list of strings, each one a tag that an object can match.

        Returns
        -------
        List[DataConcepts]
            Every object in this collection that matches one of the tags.
            See (insert link) for a discussion of how to match on tags.

        """
        params = {'tags': tags}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)

        response = self.session.get_resource(
            self._get_path(ignore_dataset=True),
            params=params)
        return [self.build(content) for content in response["contents"]]

    def filter_by_attribute_bounds(self,
                                   attribute_bounds: Dict[Union[AttributeTemplate, LinkByUID],
                                                          BaseBounds]):
        """
        Get all objects in the collection with attributes within certain bounds.

        Currently only one attribute and one bounds on that attribute is supported.

        Parameters
        ----------
        attribute_bounds: Dict[Union[AttributeTemplate, LinkByUID], BaseBounds]
            A dictionary from attributes to the bounds on that attribute.
            Each attribute may be represented as an AttributeTemplate or as a LinkByUID,
            but in either case there must be a uid and it must correspond to an
            AttributeTemplate that exists in the database.
            Only the uid is passed, so if you would like to update an attribute template you
            must register that change to the database before you can use it to filter.

        Returns
        -------
        List[DataConcepts]
            List of all objects in this collection that both have the specified attribute
            and have values within the specified bounds.

        """
        assert isinstance(attribute_bounds, dict) and len(attribute_bounds) == 1

        attribute_bounds_dict = dict()
        for key, value in attribute_bounds.items():
            template_id = get_object_id(key)
            attribute_bounds_dict[template_id] = value.as_dict()
        body = {'attribute_bounds': attribute_bounds_dict}
        params = {}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)

        response = self.session.post_resource(
            self._get_path(ignore_dataset=True) + "/filter-by-attribute-bounds",
            json=body,
            params=params)
        return [self.build(content) for content in response["contents"]]

    def filter_by_name(self, name: str, exact: bool = False):
        """
        Get all objects with specified name in this dataset.

        Parameters
        ----------
        name: str
            case-insensitive object name prefix to search.
        exact: bool
            Set to True to change prefix search to exact search (but still case-insensitive).
            Default is False.

        Returns
        -------
        List[DataConcepts]
            List of every object in this collection whose `name` matches the search term.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset to filter by name.")
        params = {'dataset_id': str(self.dataset_id), 'name': name, 'exact': exact}
        response = self.session.get_resource(
            # "Ignoring" dataset because it is in the query params (and required)
            self._get_path(ignore_dataset=True) + "/filter-by-name",
            params=params,
        )
        return [self.build(content) for content in response["contents"]]
