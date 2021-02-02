from typing import List, Union, Tuple, Optional
from uuid import UUID

from gemd.entity.link_by_uid import LinkByUID

from citrine._session import Session
from citrine.resources.api_error import ApiError


def _gemd_batch_delete(
        id_list: List[Union[LinkByUID, UUID]],
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

    Also note that Attribute Templates cannot be deleted at present.

    Parameters
    ----------
    id_list: List[Union[LinkByUID, UUID]]
        A list of the IDs of data objects to be removed. They can be passed either
        as a LinkByUID tuple, or as a UUID. The latter is assumed to be a Citrine
        ID, whereas the former can also be used to provide an external ID.

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
    scoped_uids = []
    for id in id_list:
        if isinstance(id, LinkByUID):
            scoped_uids.append({'scope': id.scope, 'id': id.id})
        elif isinstance(id, UUID):
            scoped_uids = {'scope': 'id', 'id': id}
        else:
            raise TypeError(
                "id_list must contain only LinkByUID or UUIDs entries")

    body = {'ids': scoped_uids}

    if dataset_id is not None:
        body.update({'dataset_id': dataset_id})

    path = '/projects/{project_id}/gemd/batch-delete'.format(**{"project_id": project_id})
    response = session.post_resource(path, body)

    return [(LinkByUID(f['id']['scope'], f['id']['id']),
             ApiError.from_dict(f['cause'])) for f in
            response['failures']]
