from functools import partial
from typing import Iterator

from citrine._rest.collection import Collection, ResourceType


class AdminCollection(Collection[ResourceType]):
    """Abstract class for representing collections of REST resources with as_admin access."""

    def list(
        self, *, per_page: int = 100, as_admin: bool = False
    ) -> Iterator[ResourceType]:
        """
        Paginate over the elements of the collection.

        Leaving page and per_page as default values will yield all elements in the
        collection, paginating over all available pages.

        Parameters
        ---------
        per_page: int, optional
            Max number of results to return per page. Default is 100.  This parameter
            is used when making requests to the backend service.  If the page parameter
            is specified it limits the maximum number of elements in the response.

        as_admin: bool, optional
            Whether this request should be made as an admin (returning all teams,
            rather than only those to which the user belongs).

        Returns
        -------
        Iterator[ResourceType]
            An iterator that can be used to loop over all the resources in this collection.
            Use list() to force evaluation of all results into an in-memory list.

        """
        fetcher = partial(
            self._fetch_page, additional_params={"as_admin": "true"} if as_admin else {}
        )
        return self._paginator.paginate(
            page_fetcher=fetcher,
            collection_builder=self._build_collection_elements,
            per_page=per_page,
        )
