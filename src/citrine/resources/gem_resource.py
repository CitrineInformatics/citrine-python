"""Top-level class for all object template objects and collections thereof."""
from abc import ABC
from typing import TypeVar, Type, List, Union, Optional, Iterator
from uuid import UUID, uuid4

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.data_concepts import _make_link_by_uid, DataConcepts
from citrine._rest.collection import Collection
from citrine._session import Session

# It will hold subclasses of DataConcepts, but multiple types at once
# How to annotate?
ResourceType = TypeVar('ResourceType', bound='DataConcepts')

class GemResourceCollection(Collection, ABC):
    """A collection of GEMD objects/templates of any kind."""

    _path_template = 'projects/{project_id}/storables'
    _dataset_agnostic_path_template = 'projects/{project_id}/storables'
    _individual_key = None
    _collection_key = None

    def __init__(self, project_id: UUID, dataset_id: UUID, session: Session):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.session = session

    def build(self, data: dict):
        return DataConcepts.get_type(data).build(data)

    def get(self, uid: Union[UUID, str, LinkByUID, BaseEntity], *,
                 scope: Optional[str] = None) -> DataConcepts:
        """
        Get a GEMD resource within the project by its id.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, BaseEntity]
            A representation of the object (Citrine id, LinkByUID, or the object itself)
        scope: Optional[str]
            [DEPRECATED] use a LinkByUID to specify a custom scope
            The scope of the uid, defaults to Citrine scope (CITRINE_SCOPE)

        Returns
        -------
        ResourceType
            An object with specified scope and uid

        """
        link = _make_link_by_uid(uid, scope)
        path = self._get_path() + "/{}/{}".format(link.scope, link.id)
        data = self.session.get_resource(path)
        return DataConcepts.get_type(data).build(data)

    def list_by_name(self, name: str, *, exact: bool = False,
                     forward: bool = True, per_page: int = 100):
        """
        Get all GEMD objects/templates with specified name in this dataset.

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
        Iterator[ResourceType]
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