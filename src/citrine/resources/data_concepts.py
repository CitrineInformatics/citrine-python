"""Top-level class for all data concepts objects and collections thereof."""
from abc import abstractmethod, ABC
from typing import TypeVar, Type, List, Union, Optional, Iterator
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.properties import Property as SerializableProperty
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine._utils.functions import scrub_none, replace_objects_with_links
from citrine.resources.audit_info import AuditInfo
from citrine.resources.response import Response
from taurus.entity.dict_serializable import DictSerializable
from taurus.entity.link_by_uid import LinkByUID
from taurus.json import TaurusJson


class DataConcepts(PolymorphicSerializable['DataConcepts'], DictSerializable, ABC):
    """
    An abstract data concepts object.

    DataConcepts must be extended along with `Resource`.

    Parameters
    ----------
    typ: str
        A string denoting what type of DataConcepts class a particular instantiation is.

    """

    _type_key = "type"
    """str: key used to determine type of serialized object."""

    _client_keys = []
    """list of str: keys that are in the serialized object, but are only relevant to the client.
    These keys are not passed to the data model during deserialization.
    """

    class_dict = dict()
    """
    Dict[str, class]: dictionary from the type key to the class for every class \
    that extends DataConcepts.

    Only populated if the :func:`get_type` method is invoked.
    """

    json_support = None
    """
    Custom json support object, which knows how to serialize and deserialize DataConcepts classes.
    """

    client_specific_fields = {
        "audit_info": AuditInfo,
        "dataset": properties.UUID,
    }
    """
    Fields that are added to the taurus data objects when they are used in this client

    * AuditInfo contains who/when information about the resource on the citrine platform
    """

    def __init__(self, typ: str):
        self.typ = typ
        for field in self.client_specific_fields:
            self.__setattr__("_{}".format(field), None)

    @property
    def audit_info(self) -> Optional[AuditInfo]:
        """Get the audit info object."""
        return self._audit_info

    @property
    def dataset(self) -> Optional[UUID]:
        """[ALPHA] Get the dataset of this object, if it was returned by the backend."""
        return self._dataset

    @classmethod
    def from_dict(cls, d: dict):
        """
        Build a data concepts object from a dictionary.

        This is an internal method, and should not be called directly by users.  First,
        it removes client_specific_fields from d, if present, and then calls the taurus
        object's from_dict method.  Finally, it adds those fields back.

        Parameters
        ----------
        d: dict
            A representation of the object that will be shallowly loaded into the object.

        """
        popped = {k: d.pop(k, None) for k in cls.client_specific_fields}
        obj = super().from_dict(d)

        for field, clazz in cls.client_specific_fields.items():
            value = popped[field]
            if value is None:
                deserialized = None
            elif issubclass(clazz, DictSerializable):
                if not isinstance(value, dict):
                    raise TypeError(
                        "{} must be a dictionary or None but was {}".format(field, value))
                deserialized = clazz.build(value)
            elif issubclass(clazz, SerializableProperty):
                # deserialize handles type checking already
                deserialized = clazz(clazz).deserialize(value)
            else:
                raise NotImplementedError("No deserialization strategy reported for client "
                                          "field type {} for field.".format(clazz, field))
            setattr(obj, "_{}".format(field), deserialized)
        return obj

    @classmethod
    def build(cls, data: dict):
        """
        Build a data concepts object from a dictionary or from a Taurus object.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A representation of the object. It must be possible to put this dictionary through
            the loads/dumps cycle of the Taurus
            :py:mod:`JSON encoder <taurus.jsonr>`. The ensuing dictionary must
            have a `type` field that corresponds to the response key of this class or of
            :py:class:`LinkByUID <taurus.entity.link_by_uid.LinkByUID>`.

        Returns
        -------
        DataConcepts
            An object corresponding to a data concepts resource.

        """
        return cls.get_json_support().copy(data)

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
            This method will also work if data is a deserialized Taurus object.

        Returns
        -------
        class
            The class corresponding to data.

        """
        if len(DataConcepts.class_dict) == 0:
            # This line is only reached if get_type is called before build,
            # which is hard to reproduce, hence the no cover.
            DataConcepts._make_class_dict()  # pragma: no cover
        if isinstance(data, DictSerializable):
            data = data.as_dict()
        return DataConcepts.class_dict[data['type']]

    @staticmethod
    def _make_class_dict():
        """Construct a dictionary from each type key to the class."""
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
        _clazz_list = [ConditionTemplate, ParameterTemplate, PropertyTemplate,
                       MaterialTemplate, MeasurementTemplate, ProcessTemplate,
                       IngredientSpec, MaterialSpec, MeasurementSpec, ProcessSpec,
                       IngredientRun, MaterialRun, MeasurementRun, ProcessRun]
        for clazz in _clazz_list:
            DataConcepts.class_dict[clazz._response_key] = clazz
        DataConcepts.class_dict['link_by_uid'] = LinkByUID

    @classmethod
    def get_json_support(cls):
        """Get a DataConcepts-compatible json serializer/deserializer."""
        if cls.json_support is None:
            DataConcepts._make_class_dict()
            cls.json_support = TaurusJson()
            cls.json_support.register_classes(
                {k: v for k, v in DataConcepts.class_dict.items() if k != "link_by_uid"}
            )
        return cls.json_support

    def as_dict(self) -> dict:
        """Dump to a dictionary (useful for interoperability with taurus)."""
        return self.dump()


ResourceType = TypeVar('ResourceType', bound='DataConcepts')


class DataConceptsCollection(Collection[ResourceType], ABC):
    """
    A collection of one kind of data concepts object.

    Parameters
    ----------
    project_id: UUID
        The uid of the project that this collection belongs to.
    dataset_id: UUID
        The uid of the dataset that this collection belongs to. If None then the collection
        ranges over all datasets in the project. Note that this is only allowed for certain
        actions. For example, you can use :func:`list_by_tag` to search over all datasets,
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
        return data_concepts_object

    def _fetch_page(self, page: Optional[int] = None, per_page: Optional[int] = None):
        """
        List all visible elements of the collection.  Does not handle pagination.

        Parameters
        ----------
        page: Optional[int]
            The page of results to list, 1-indexed (i.e. the first page is page=1)
        per_page: Optional[int]
            The number of results to list per page

        Returns
        -------
        List[DataConcepts]
            Every object in this collection.

        """
        return self.filter_by_tags([], page, per_page)

    def list(self,
             page: Optional[int] = None,
             per_page: Optional[int] = 100) -> List[DataConcepts]:
        """
        List all visible elements of the collection.

        Leaving page and per_page as default values will return a list of all elements
        in the collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and return
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page.  This parameter is used when
            making requests to the backend service.  If the page parameter is
            specified it limits the maximum number of elements in the response.

        Returns
        -------
        List[DataConcepts]
            Every object in this collection.

        """
        # Convert the iterator to a list to avoid breaking existing client relying on lists
        return list(super().list(page=page, per_page=per_page))

    def register(self, model: ResourceType, dry_run=False):
        """
        Create a new element of the collection or update an existing element.

        If the input model has an ID that corresponds to an existing object in the
        database, then that object will be updated. Otherwise a new object will be created.

        Only the top-level object in `model` itself is written to the database with this
        method. References to other objects are persisted as links, and the object returned
        by this method has all instances of data objects replaced by instances of LinkByUid.
        Registering an object which references other objects does NOT implicitly register
        those other objects. Rather, those other objects' values are ignored, and the
        pre-existence of objects with their IDs is asserted before attempting to write
        `model`.

        Parameters
        ----------
        model: DataConcepts
            The DataConcepts object.
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        Returns
        -------
        DataConcepts
            A copy of the registered object as it now exists in the database.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset in order to register a data model object.")
        path = self._get_path()
        params = {'dry_run': dry_run}
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
        data = self.session.post_resource(path, dumped_data, params=params)
        full_model = self.build(data)
        return full_model

    def get(self, uid: Union[UUID, str], scope: str = 'id') -> ResourceType:
        """
        Get the element of the collection with ID equal to uid.

        Parameters
        ----------
        uid: Union[UUID, str]
            The ID.
        scope: str
            The scope of the uid, defaults to Citrine scope ('id')

        Returns
        -------
        DataConcepts
            An object with specified scope and uid

        """
        path = self._get_path(ignore_dataset=self.dataset_id is None) + "/{}/{}".format(scope, uid)
        data = self.session.get_resource(path)
        return self.build(data)

    def filter_by_tags(self, tags: List[str],
                       page: Optional[int] = None, per_page: Optional[int] = None):
        """
        Get all objects in the collection that match any one of a list of tags.

        Parameters
        ----------
        tags: List[str]
            A list of strings, each one a tag that an object can match. Currently
            limited to a length of 1 or 0 (empty list does not filter).
        page: Optional[int]
            The page of results to list, 1-indexed (i.e. the first page is page=1)
        per_page: Optional[int]
            The number of results to list per page

        Returns
        -------
        List[DataConcepts]
            Every object in this collection that matches one of the tags.
            See (insert link) for a discussion of how to match on tags.

        """
        if type(tags) == str:
            tags = [tags]
        if len(tags) > 1:
            raise NotImplementedError('Searching by multiple tags is not currently supported.')
        params = {'tags': tags}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        if page is not None:
            params['page'] = page
        if per_page is not None:
            params['per_page'] = per_page

        response = self.session.get_resource(
            self._get_path(ignore_dataset=True),
            params=params)
        return [self.build(content) for content in response["contents"]]

    def filter_by_name(self, name: str, exact: bool = False,
                       page: Optional[int] = None, per_page: Optional[int] = None):
        """
        Get all objects with specified name in this dataset.

        Parameters
        ----------
        name: str
            case-insensitive object name prefix to search.
        exact: bool
            Set to True to change prefix search to exact search (but still case-insensitive).
            Default is False.
        page: Optional[int]
            The page of results to list, 1-indexed (i.e. the first page is page=1)
        per_page: Optional[int]
            The number of results to list per page

        Returns
        -------
        List[DataConcepts]
            List of every object in this collection whose `name` matches the search term.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset to filter by name.")
        params = {'dataset_id': str(self.dataset_id), 'name': name, 'exact': exact}
        if page is not None:
            params['page'] = page
        if per_page is not None:
            params['per_page'] = per_page
        response = self.session.get_resource(
            # "Ignoring" dataset because it is in the query params (and required)
            self._get_path(ignore_dataset=True) + "/filter-by-name",
            params=params)
        return [self.build(content) for content in response["contents"]]

    def list_by_name(self, name: str, exact: bool = False,
                     forward: bool = True, per_page: int = 100) -> Iterator[DataConcepts]:
        """
        Get all objects with specified name in this dataset.

        Parameters
        ----------
        name: str
            case-insensitive object name prefix to search.
        exact: bool
            Set to True to change prefix search to exact search (but still case-insensitive).
            Default is False.
        forward: bool
            Set to False to reverse the order of results (i.e. return in descending order).
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[DataConcepts]
            List of every object in this collection whose `name` matches the search term.

        """
        if self.dataset_id is None:
            raise RuntimeError("Must specify a dataset to filter by name.")
        params = {'dataset_id': str(self.dataset_id), 'name': name, 'exact': exact}
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            # "Ignoring" dataset because it is in the query params (and required)
            self._get_path(ignore_dataset=True) + "/filter-by-name",
            forward=forward,
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[DataConcepts]:
        """
        Get all objects in the collection.

        The order of results should not be relied upon, but for now they are sorted by
        dataset, object type, and creation time (in that order of priority).

        Parameters
        ----------
        forward: bool
            Set to False to reverse the order of results (i.e. return in descending order).
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[DataConcepts]
            Every object in this collection.

        """
        params = {}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            self._get_path(ignore_dataset=True),
            forward=forward,
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def list_by_tag(self, tag: str, per_page: int = 100) -> Iterator[DataConcepts]:
        """
        Get all objects bearing a tag prefixed with `tag` in the collection.

        The order of results is largely unmeaningul. Results from the same dataset will be
        grouped together but no other meaningful ordering can be relied upon. Duplication in
        the result set may (but needn't) occur when one object has multiple tags matching the
        search tag. For this reason, it is inadvisable to put 2 tags with the same prefix
        (e.g. 'foo::bar' and 'foo::baz') the same object when it can be avoided.

        Parameters
        ----------
        tag: str
            The prefix with which to search. Must fully match up to the first delimiter (ex.
            'foo' and 'foo::b' both match 'foo::bar' but 'fo' is insufficient.
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[DataConcepts]
            Every object in this collection.

        """
        params = {'tag': tag}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            self._get_path(ignore_dataset=True),
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def delete(self, uid: Union[UUID, str], scope: str = 'id', dry_run: bool = False):
        """
        Delete the element of the collection with ID equal to uid.

        Parameters
        ----------
        uid: Union[UUID, str]
            The ID.
        scope: str
            The scope of the uid, defaults to Citrine scope ('id')
        dry_run: bool
            Whether to actually delete the item or run a dry run of the delete operation.
            Dry run is intended to be used for validation. Default: false

        """
        path = self._get_path() + "/{}/{}".format(scope, uid)
        params = {'dry_run': dry_run}
        self.session.delete_resource(path, params=params)
        return Response(status_code=200)  # delete succeeded
