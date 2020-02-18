from typing import Dict, Any
from copy import deepcopy
from urllib.parse import urlparse
from uuid import uuid4, UUID
import os

from taurus.entity.link_by_uid import LinkByUID


def set_default_uid(id_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Validates a dictionary of ids, adding a default id if necessary.

    The scope 'id' is reserved for a Citrine id, and it must be a UUID4.
    If there is no id with scope 'id', it is set to an automatically generated UUID4.
    If 'id' corresponds to an id that is not a UUID4, an exception is thrown.

    :return the input id dictionary, with the Citrine id added, if necessary.

    """
    reserved_scope = 'id'
    if isinstance(id_dict, dict):
        if reserved_scope in id_dict:
            try:
                # If id_dict['id'] is a string of a valid uuid, then this call will be successful
                UUID(id_dict[reserved_scope])
            except Exception:
                raise ValueError("{} scope must correspond to a UUID, "
                                 "instead got {}".format(reserved_scope, id_dict[reserved_scope]))
            return id_dict
        else:
            id_dict_copy = deepcopy(id_dict)
            id_dict_copy[reserved_scope] = str(uuid4())
            return id_dict_copy
    elif id_dict is None:
        return {reserved_scope: str(uuid4())}
    else:
        raise Exception("Cannot validate id for {}".format(id_dict))


def get_object_id(object_or_id):
    """Extract the citrine id from a data concepts object or LinkByUID."""
    from taurus.entity.attribute.base_attribute import BaseAttribute
    from citrine.resources.data_concepts import DataConcepts
    if isinstance(object_or_id, BaseAttribute):
        raise ValueError("Attributes do not have ids.")
    citrine_scope = 'id'
    if isinstance(object_or_id, DataConcepts):
        citrine_id = object_or_id.uids.get(citrine_scope)
        if citrine_id is not None:
            return citrine_id
        raise ValueError("Data concepts object {!r} must have a citrine uuid with "
                         "scope".format(object_or_id, citrine_scope))
    if isinstance(object_or_id, LinkByUID):
        if object_or_id.scope == citrine_scope:
            return object_or_id.id
        raise ValueError("LinkByUID must be scoped to citrine scope {}, "
                         "instead is {}".format(citrine_scope, object_or_id.scope))
    raise TypeError("{} must be a data concepts object or LinkByUID".format(object_or_id))


def validate_type(data_dict: dict, type_name: str) -> dict:
    """Ensure that dict has field 'type' with given value."""
    data_dict_copy = data_dict.copy()
    if 'type' in data_dict_copy:
        if data_dict_copy['type'] != type_name:
            raise Exception(
                "Object type must be {}, but was instead {}.".format(type_name, data_dict['type']))
    else:
        data_dict_copy['type'] = type_name

    return data_dict_copy


def scrub_none(json):
    """
    Recursively delete dictionary keys and remove list entries with the value ``None``.

    This action modifies the data structure in place.
    """
    if isinstance(json, dict):
        for key, value in list(json.items()):
            if value is None:
                del json[key]
            else:
                json[key] = scrub_none(json[key])
    elif isinstance(json, list):
        for idx, element in reversed(list(enumerate(json))):
            if element is None:
                del (json[idx])
            else:
                json[idx] = scrub_none(element)
    return json


def replace_objects_with_links(json: dict) -> dict:
    """For each top-level object in a dictionary, replace it with a Link, if appropriate."""
    for key, value in list(json.items()):
        json[key] = object_to_link(value)
    return json


def object_to_link(obj: Any) -> Any:
    """See if an object is a dictionary that can be converted into a Link, and if so, convert."""
    if isinstance(obj, dict):
        if 'type' in obj and 'uids' in obj and obj['type'] != LinkByUID.typ:
            return object_to_link_by_uid(obj)
        else:
            return replace_objects_with_links(obj)
    elif isinstance(obj, (tuple, list)):
        return [object_to_link(entry) for entry in obj]
    return obj


def object_to_link_by_uid(json: dict) -> dict:
    """Convert an object dictionary into a LinkByUID dictionary, if possible."""
    if 'uids' in json:
        uids = json['uids']
        if not isinstance(uids, dict) or not uids:
            return json
        if 'id' in uids:
            scope = 'id'
        else:
            scope = list(uids.keys())[0]
        this_id = uids[scope]
        return LinkByUID(scope, this_id).as_dict()
    else:
        return json


def rewrite_s3_links_locally(url: str) -> str:
    """
    Rewrites 'localstack' hosts to localhost for testing.

    This is required for dockerized environments. In docker environments,
    virtual hosts are created with virtual port numbers.

    localstack:4572 is an example of a virtualHost:virtualPort

    In order to access dockerized servers from outside of docker, the
    host:port space must be mapped onto localhost. For S3, this mapping is as follows:
    localstack:4572 => localhost:9572
    """
    parsed_url = urlparse(url)
    if parsed_url.netloc != "localstack:4572":
        return url
    else:
        return parsed_url._replace(netloc="localhost:9572").geturl()


def write_file_locally(content, local_path: str):
    """Take content from remote and ensure path exists."""
    directory, filename = os.path.split(local_path)
    if filename == "":
        raise ValueError("A filename must be provided in the path")
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(local_path, 'wb') as output_file:
        output_file.write(content)
