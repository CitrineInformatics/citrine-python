import inspect
from functools import wraps
import os
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse, quote
from warnings import warn

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
    Rewrite s3 links from localstack.

    When the tests are run inside Devkit, Localstack uses the hostname "localstack" and port
    4566 for the local S3 files URL. If you're hitting localhost from outside devkit, the
    host "localstack" won't resolve, but the port 4566 is still mapped to the host port (also
    on 4566), so we need to write the file links S3 endpoint hostname to "localhost".

    The caller should supply the correct S3 endpoint URL, eg: session.s3_endpoint_url
    """
    parsed_url = urlparse(url)

    if s3_endpoint_url is not None:
        # Given an explicit endpoint to use instead
        parsed_s3_endpoint = urlparse(s3_endpoint_url)
        return parsed_url._replace(scheme=parsed_s3_endpoint.scheme,
                                   netloc=parsed_s3_endpoint.netloc).geturl()
    else:
        # Else return the URL unmodified
        return url


def write_file_locally(content, local_path: Union[str, Path]):
    """Take content from remote and ensure path exists."""
    if isinstance(local_path, str):
        if len(os.path.split(local_path)[-1]) == 0:
            raise ValueError(f"A filename must be provided in the path ({local_path})")
        local_path = Path(local_path)

    # Resolve ~, .., and the like
    local_path = local_path.expanduser().resolve()
    if local_path.is_dir():
        raise ValueError(f"A filename must be provided in the path ({local_path})")

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.open(mode='wb').write(content)


def shadow_classes_in_module(source_module, target_module):
    """Shadow classes from a source to a target module, for backwards compatibility purposes."""
    for c in [cls for _, cls in inspect.getmembers(source_module, inspect.isclass) if
              cls.__module__ == source_module.__name__]:
        setattr(target_module, c.__qualname__, c)


def migrate_deprecated_argument(
        new_arg: Optional[Any],
        new_arg_name: str,
        old_arg: Optional[Any],
        old_arg_name: str
) -> Any:
    """
    Facilitates the migration of an argument's name.

    This method handles the situation in which a function has two arguments for the same thing,
    one old and one new. It ensures that only one of the two arguments is provided, throwing a
    ValueError is both/neither are provided. If the old version of the argument is provided,
    it throws a deprecation warning.

    Parameters
    ----------
    new_arg: Optional[Any]
        the value provided using the new argument (or None, if not provided)
    new_arg_name: str
        the new name of the argument (used for creating user-facing messages)
    old_arg: Optional[Any]
        the value provided using the old argument (or None, if not provided)
    old_arg_name: str
        the old name of the argument (used for creating user-facing messages)

    Returns
    -------
    Any
        the value of the argument to be used by the calling method

    """
    if old_arg is not None:
        warn(f"\'{old_arg_name}\' is deprecated in favor of \'{new_arg_name}\'",
             DeprecationWarning)
        if new_arg is None:
            return old_arg
        else:
            raise ValueError(f"Cannot specify both \'{new_arg_name}\' and \'{new_arg_name}\'")
    elif new_arg is None:
        raise ValueError(f"Please specify \'{new_arg_name}\'")
    return new_arg


def format_escaped_url(
        template: str,
        *args,
        **kwargs
) -> str:
    """
    Escape arguments with percent encoding and bind them to a template of a URL.

    This method takes a template string and binds the positional and keyword arguments
    passing it into a format statement.

    Parameters
    ----------
    template: str
        the `format` template to which the escaped arguments will be bound
    *args : Iterable[str]
        Other arguments
    **kwargs: Dict[str]
        Keyword arguments

    Returns
    -------
    str
        the formatted URL

    """
    return template.format(*[quote(str(x), safe='') for x in args],
                           **{k: quote(str(v), safe='') for (k, v) in kwargs.items()}
                           )


def use_teams(alt, negate=False):
    """
    Raises error with a redirect message if method is unavailable with(out) teams support.

    Parameters
    ----------
    alt: str
        the alternative method the user should use. Added to the Error message
    negate: bool
        Set to True if the error should be raised if teams are in use. Keep False
        if error should be raised if teams are not available.

    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if negate:
                if not self.session._accounts_service_v3:
                    raise NotImplementedError(f"Not available, you may be looking for {alt}")
            else:
                if self.session._accounts_service_v3:
                    raise NotImplementedError(f"Not available, you may be looking for {alt}")
            return f(self, *args, **kwargs)

        return wrapper

    return decorator
