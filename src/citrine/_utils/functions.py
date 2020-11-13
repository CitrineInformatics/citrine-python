import inspect
import os
from typing import Any
from urllib.parse import urlparse

from gemd.entity.link_by_uid import LinkByUID


def get_object_id(object_or_id):
    """Extract the citrine id from a data concepts object or LinkByUID."""
    from gemd.entity.attribute.base_attribute import BaseAttribute
    from citrine.resources.data_concepts import DataConcepts, CITRINE_SCOPE

    if isinstance(object_or_id, BaseAttribute):
        raise ValueError("Attributes do not have ids.")
    if isinstance(object_or_id, DataConcepts):
        citrine_id = object_or_id.uids.get(CITRINE_SCOPE)
        return citrine_id
    if isinstance(object_or_id, LinkByUID):
        if object_or_id.scope == CITRINE_SCOPE:
            return object_or_id.id
        raise ValueError("LinkByUID must be scoped to citrine scope {}, "
                         "instead is {}".format(CITRINE_SCOPE, object_or_id.scope))
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
    Recursively delete dictionary keys with the value ``None``.

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
            if element is not None:
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
    from citrine.resources.data_concepts import CITRINE_SCOPE
    if 'uids' in json:
        uids = json['uids']
        if not isinstance(uids, dict) or not uids:
            return json
        if CITRINE_SCOPE in uids:
            scope = CITRINE_SCOPE
        else:
            scope = next(iter(uids))
        this_id = uids[scope]
        return LinkByUID(scope, this_id).as_dict()
    else:
        return json


def rewrite_s3_links_locally(url: str, s3_endpoint_url: str = None) -> str:
    """
    Rewrites 'localstack' hosts to localhost for testing.

    This is required for dockerized environments. In docker environments,
    virtual hosts are created with virtual port numbers.

    localstack:4572 is an example of a virtualHost:virtualPort

    In order to access dockerized servers from outside of docker, the
    host:port space must be mapped onto localhost. For S3, this mapping is as follows:
    localstack:4572 => localhost:9572

    Allows for an explicit override, useful for tests that are trying to access this endpoint
    from within the docker context
    """
    parsed_url = urlparse(url)
    if s3_endpoint_url is not None:
        parsed_s3_endpoint = urlparse(s3_endpoint_url)
        return parsed_url._replace(scheme=parsed_s3_endpoint.scheme,
                                   netloc=parsed_s3_endpoint.netloc).geturl()
    elif parsed_url.netloc != "localstack:4572":
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


def shadow_classes_in_module(source_module, target_module):
    """Shadow classes from a source to a target module, for backwards compatibility purposes."""
    for c in [cls for _, cls in inspect.getmembers(source_module, inspect.isclass) if
              cls.__module__ == source_module.__name__]:
        setattr(target_module, c.__qualname__, c)
