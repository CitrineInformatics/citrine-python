from abc import abstractmethod
from typing import Optional, Union, Generic, TypeVar, Iterable
from uuid import UUID
import warnings

from citrine.exceptions import ModuleRegistrationFailedException, NonRetryableException
from citrine.resources.response import Response


ResourceType = TypeVar('ResourceType', bound='Resource')

# Python does not support a TypeVar being used as a bound for another TypeVar.
# Thus, this will never be particularly type safe on its own. The solution is to
# have subclasses override the create method.
CreationType = TypeVar('CreationType', bound='Resource')


class Collection(Generic[ResourceType]):
    """Abstract class for representing collections of REST resources."""

    _path_template: str = NotImplemented
    _dataset_agnostic_path_template: str = NotImplemented
    _individual_key: str = NotImplemented
    _resource: ResourceType = NotImplemented
    _collection_key: str = 'entries'

    def _get_path(self, uid: Optional[Union[UUID, str]] = None,
                  ignore_dataset: Optional[bool] = False) -> str:
        """Construct a url from __base_path__ and, optionally, id."""
        subpath = '/{}'.format(uid) if uid else ''
        if ignore_dataset:
            return self._dataset_agnostic_path_template.format(**self.__dict__) + subpath
        else:
            return self._path_template.format(**self.__dict__) + subpath

    @abstractmethod
    def build(self, data: dict):
        """Build an individual element of the collection."""

    def get(self, uid: Union[UUID, str]) -> ResourceType:
        """Get a particular element of the collection."""
        path = self._get_path(uid)
        data = self.session.get_resource(path)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def register(self, model: CreationType) -> CreationType:
        """Create a new element of the collection by registering an existing resource."""
        path = self._get_path()
        try:
            data = self.session.post_resource(path, model.dump())
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)
        except NonRetryableException as e:
            raise ModuleRegistrationFailedException(model.__class__.__name__, e)

    def _fetch_page(self,
                    page: Optional[int] = None,
                    per_page: Optional[int] = None) -> Iterable[ResourceType]:
        """
        Fetch visible elements in the collection.  This does not handle pagination.

        This method will return the first page of results using the default page/per_page
        behaviour of the backend service.  Specify page/per_page to override these defaults
        which are passed to the backend service.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is the first page, which is 1.
        per_page: int, optional
            Max number of results to return. Default is 20.

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        path = self._get_path()

        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        data = self.session.get_resource(path, params=params)
        # A 'None' collection key implies response has a top-level array
        # of 'ResourceType'
        # TODO: Unify backend return values
        if self._collection_key is None:
            collection = data
        else:
            collection = data[self._collection_key]

        for element in collection:
            try:
                yield self.build(element)
            except(KeyError, ValueError):
                # TODO:  Right now this is a hack.  Clean this up soon.
                # Module collections are not filtering on module type
                # properly, so we are filtering client-side.
                pass

    def list(self,
             page: Optional[int] = None,
             per_page: int = 100) -> Iterable[ResourceType]:
        """
        List all visible elements in the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        page: int, optional
            The "page" of results to list. Default is to read all pages and yield
            all results.  This option is deprecated.
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        Returns
        -------
        Iterable[ResourceType]
            Resources in this collection.

        """
        if page is not None:
            warnings.warn("The page parameter is deprecated, default is automatic pagination",
                          DeprecationWarning)

        first_uid = None
        page_idx = page
        while True:
            subset = self._fetch_page(page=page_idx, per_page=per_page)

            count = 0
            for idx, element in enumerate(subset):
                # escaping from infinite loops where page/per_page are not
                # honored and are returning the same results regardless of page:
                uid = getattr(element, 'uid', None)
                if first_uid is not None and first_uid == uid:
                    # TODO: raise an exception once the APIs that ignore pagination are fixed
                    break

                yield element

                if idx == 0:
                    first_uid = uid

                count += 1

            # If the page number is specified we exit to disable auto-paginating
            if page is not None:
                break

            # Handle the case where we get an unexpected number of results (e.g. last page)
            if count == 0 or count < per_page:
                break

            if page_idx is None:
                page_idx = 2
            else:
                page_idx += 1

    def update(self, model: CreationType) -> CreationType:
        """Update a particular element of the collection."""
        url = self._get_path(model.uid)
        updated = self.session.put_resource(url, model.dump())
        data = updated[self._individual_key] if self._individual_key else updated
        return self.build(data)

    def delete(self, uid: Union[UUID, str]) -> Response:
        """Delete a particular element of the collection."""
        url = self._get_path(uid)
        data = self.session.delete_resource(url)
        return Response(body=data)
