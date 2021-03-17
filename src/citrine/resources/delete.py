import json
from typing import List, Union, Tuple, Optional
from uuid import UUID

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID

from citrine._session import Session
from citrine.resources.api_error import ApiError
from citrine.resources.job import _poll_for_job_completion


def _async_gemd_batch_delete(
        id_list: List[Union[LinkByUID, UUID, str, BaseEntity]],
        project_id: UUID,
        session: Session,
        dataset_id: Optional[UUID],
        timeout: float = 2 * 60,
        polling_delay: float = 1.0
) -> List[Tuple[LinkByUID, ApiError]]:
    """
    Shared implementation of Async GEMD Batch deletion.

    See documentation for _gemd_batch_delete. The only difference is that this version polls for
    an asynchronous result and can tolerate a very long runtime that the synchronous version
    cannot. Because this version can tolerate a long runtime, this versions allows for the
    removal of attribute templates.

    Parameters
    ----------
    id_list: List[Union[LinkByUID, UUID]]
        A list of the IDs of data objects to be removed. They can be passed either
        as a LinkByUID tuple, or as a UUID. The latter is assumed to be a Citrine
        ID, whereas the former can also be used to provide an external ID.

    project_id: UUID
        The Project ID to use in the delete request.

    dataset_id: Optional[UUID] = None
        An optional dataset ID, which if provided will mandate that all GEMD objects
        must be within the given dataset.

    timeout
        Amount of time to wait on the job (in seconds) before giving up. Defaults
        to 2 minutes. Note that this number has no effect on the underlying job
        itself, which can also time out server-side.

    polling_delay:
        How long to delay between each polling retry attempt.

    Returns
    -------
    List[Tuple[LinkByUID, ApiError]]
        A list of (LinkByUID, api_error) for each failure to delete an object.
        Note that this method doesn't raise an exception if an object fails to be
        deleted.

    """
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

    body = {'ids': scoped_uids}

    if dataset_id is not None:
        body.update({'dataset_id': str(dataset_id)})

    path = '/projects/{project_id}/gemd/async-batch-delete'.format(**{"project_id": project_id})
    response = session.post_resource(path, body)

    job_id = response["job_id"]

    response = _poll_for_job_completion(session, project_id, job_id, timeout=timeout,
                                        polling_delay=polling_delay)

    return [(LinkByUID(f['id']['scope'], f['id']['id']), ApiError.from_dict(f['cause']))
            for f in json.loads(response.output['failures'])]
