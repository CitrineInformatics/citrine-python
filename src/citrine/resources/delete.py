from typing import List, Union, Tuple, Optional
from uuid import UUID

from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.base_entity import BaseEntity
from gemd.util import writable_sort_order

from citrine._session import Session
from citrine.resources.api_error import ApiError

DELETE_SERVICE_MAX = 50  # Edit here to change service limit


def _gemd_batch_delete(
        id_list: List[Union[LinkByUID, UUID, str, BaseEntity]],
        project_id: UUID,
        session: Session,
        dataset_id: Optional[UUID] = None
) -> List[Tuple[LinkByUID, ApiError]]:
    """
    Shared implementation of GEMD Batch deletion.

    You may provide GEMD objects that reference each other, and the objects
    will be removed in the appropriate order.

    A failure will be returned if the object cannot be deleted due to an external
    reference.

    If an optional dataset_id is provided, deletes are restricted to only occur on objects
    contained by that specific dataset.

    You must have Write access on the datasets associated with the GEMD objects provided.

    If you wish to delete more than 50 objects, queuing of deletes requires that
    the types of objects be known, and thus you _must_ provide ids in the form
    of BaseEntities.

    Also note that Attribute Templates cannot be deleted at present.

    Parameters
    ----------
    id_list: List[Union[LinkByUID, UUID, str, BaseEntity]]
        A list of the IDs of data objects to be removed. They can be passed
        as a LinkByUID tuple, a UUID, a string, or the object itself. A UUID
        or string is assumed to be a Citrine ID, whereas a LinkByUID or
        BaseEntity can also be used to provide an external ID.

    dataset_id: Optional[UUID] = None
        An optional dataset ID, which if provided will mandate that all GEMD objects
        must be within the given dataset.

    Returns
    -------
    List[Tuple[LinkByUID, ApiError]]
        A list of (LinkByUID, api_error) for each failure to delete an object.
        Note that this method doesn't raise an exception if an object fails to be
        deleted.

    """
    if len(id_list) > DELETE_SERVICE_MAX:  # we need to sort it
        if any([not isinstance(x, BaseEntity) for x in id_list]):
            raise TypeError(
                "If more than {} deletes are requested, id_list must contain "
                "only BaseEntities (objects & templates)".format(DELETE_SERVICE_MAX)
            )
        id_list = sorted(id_list, key=lambda x: writable_sort_order(x), reverse=True)

    scoped_uids = []
    for uid in id_list:  # And now normalize to id/scope pairs
        if isinstance(uid, BaseEntity):
            link_by_uid = LinkByUID.from_entity(uid)
            scoped_uids.append({'scope': link_by_uid.scope, 'id': link_by_uid.id})
        elif isinstance(uid, LinkByUID):
            scoped_uids.append({'scope': uid.scope, 'id': uid.id})
        elif isinstance(uid, UUID):
            scoped_uids.append({'scope': 'id', 'id': uid})
        elif isinstance(uid, str):
            try:
                scoped_uids.append({'scope': 'id', 'id': UUID(uid)})
            except ValueError:
                raise TypeError("{} does not look like a UUID".format(uid))
        else:
            raise TypeError(
                "id_list must contain only LinkByUIDs, UUIDs, strings, or BaseEntities")

    failures = []
    while len(scoped_uids) > 0:
        queue = scoped_uids[:DELETE_SERVICE_MAX]
        del(scoped_uids[:DELETE_SERVICE_MAX])

        body = {'ids': queue}

        if dataset_id is not None:
            body.update({'dataset_id': str(dataset_id)})

        path = '/projects/{project_id}/gemd/batch-delete'.format(**{"project_id": project_id})
        response = session.post_resource(path, body)
        failures.extend(response['failures'])

    return [(LinkByUID(f['id']['scope'], f['id']['id']), ApiError.from_dict(f['cause']))
            for f in failures]
