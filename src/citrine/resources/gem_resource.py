"""Collection class for generic GEMD objects and templates."""
from abc import ABC
from typing import Union, Optional, Iterator, List, TypeVar
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.data_concepts import DataConcepts, _make_link_by_uid
from citrine._rest.collection import Collection
from citrine._session import Session

GemResourceType = TypeVar('GemResourceType', bound='DataConcepts')


class GemResourceCollection(Collection[GemResourceType], ABC):
    """A collection of GEMD objects/templates of any type."""

    _path_template = 'projects/{project_id}/storables'
    _dataset_agnostic_path_template = 'projects/{project_id}/storables'
    _individual_key = None
    _collection_key = None
    _resource = GemResourceType

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def build(self, data: dict):
        """
        Build an arbitary GEMD object from a serialized dictionary.

        This is an internal method, and should not be called directly by users.

        Parameters
        ----------
        data: dict
            A serialized data model object.

        Returns
        -------
        GemResourceType
            A data model object built from the dictionary.

        """
        return DataConcepts.build(data)

    def get(self, uid: Union[UUID, str, LinkByUID, BaseEntity]) -> GemResourceType:
        """
        Get a GEMD resource within the project by its id.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, BaseEntity]
            A representation of the object (Citrine id, LinkByUID, or the object itself)

        Returns
        -------
        GemResourceType
            An object with specified scope and uid

        """
        link = _make_link_by_uid(uid)
        path = self._get_path() + "/{}/{}".format(link.scope, link.id)
        data = self.session.get_resource(path)
        return self.build(data)

    def list(self, *,
             per_page: Optional[int] = 100,
             forward: bool = True) -> Iterator[GemResourceType]:
        """
        Get all visible elements of the collection.

        The order of results should not be relied upon, but for now they are sorted by
        dataset, object type, and creation time (in that order of priority).

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. It is very unlikely that
            setting this parameter to something other than the default is useful.
            It exists for rare situations where the client is bandwidth constrained
            or experiencing latency from large payload sizes.
        forward: bool
            Set to False to reverse the order of results (i.e., return in descending order)

        Returns
        -------
        Iterator[GemResourceType]
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

    def list_by_name(self, name: str, *, exact: bool = False,
                     forward: bool = True, per_page: int = 100) -> Iterator[GemResourceType]:
        """
        Get all GEMD resources with specified name in this dataset.

        Parameters
        ----------
        name: str
            case-insensitive object name prefix to search.
        exact: bool
            Set to True to change prefix search to exact search (but still case-insensitive).
            Default is False.
        forward: bool
            Set to False to reverse the order of results (i.e., return in descending order).
        per_page: int
            Controls the number of results fetched with each http request to the backend.
            Typically, this is set to a sensible default and should not be modified. Consider
            modifying this value only if you find this method is unacceptably latent.

        Returns
        -------
        Iterator[GemResourceType]
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

    def list_by_tag(self, tag: str, *, per_page: int = 100) -> Iterator[GemResourceType]:
        """
        Get all GEMD resources bearing a tag prefixed with `tag` in the collection.

        The order of results is largely not meaningful. Results from the same dataset will be
        grouped together but no other meaningful ordering can be relied upon. Duplication in
        the result set may (but needn't) occur when one object has multiple tags matching the
        search tag. For this reason, it is inadvisable to put 2 tags with the same prefix
        (e.g., 'foo::bar' and 'foo::baz') in the same object when it can be avoided.

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
        Iterator[GemResourceType]
            Every object in this collection.

        """
        params = {'tags': [tag]}
        if self.dataset_id is not None:
            params['dataset_id'] = str(self.dataset_id)
        raw_objects = self.session.cursor_paged_resource(
            self.session.get_resource,
            self._get_path(ignore_dataset=True),
            per_page=per_page,
            params=params)
        return (self.build(raw) for raw in raw_objects)

    def update(self, model: GemResourceType) -> GemResourceType:
        """To update an arbitrary GEMD object, please use dataset.update instead."""
        raise NotImplementedError("To update an arbitary GEMD object,"
                                  " please use dataset.update instead.")

    def delete(self, model: GemResourceType) -> GemResourceType:
        """To delete an arbitrary GEMD object, please use dataset.delete instead."""
        raise NotImplementedError("To delete an arbitary GEMD object,"
                                  " please use dataset.delete instead.")

    def register(self, model: GemResourceType, *, dry_run=False):
        """To register an arbitrary GEMD object, please use dataset.register instead."""
        raise NotImplementedError("To register an arbitary GEMD object,"
                                  " please use dataset.register instead.")

    def register_all(self, models: List[GemResourceType], *,
                     dry_run=False) -> List[GemResourceType]:
        """To register a list of GEMD objects, please use dataset.register_all instead."""
        raise NotImplementedError("To register a list of GEMD objects,"
                                  " please use dataset.register_all instead.")
