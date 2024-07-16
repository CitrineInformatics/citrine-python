from abc import ABCMeta
import os
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union
from urllib.parse import quote, urlencode, urlparse
from uuid import UUID
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


class MigratedClassMeta(ABCMeta):
    """
    A metaclass for classes that were moved to new packages.

    This will issue deprecation warnings when you import & use the class from the
    old location.  A new class should be created in the old location:

    ```
    from citrine._utils.functions import MigratedClassMeta
    from new.package import MyClass as NewMyClass

    class MyClass(NewMyClass, deprecated_in="1.2.3", removed_in="2.0.0",
                  metaclass=MigratedClassMeta):
        pass
    ```


    If the migrated class has a custom metaclass of its own, it is necessary to
    create a joint metaclass to avoid inheritance confusion:

    ```
    from citrine._utils.functions import MigratedClassMeta, generate_shared_meta
    from new.package import MyClass as NewMyClass

    class MyClass(NewMyClass, deprecated_in="1.2.3", removed_in="2.0.0",
                  metaclass=generate_shared_meta(NewMyClass)):
        pass
    ```

    """

    _deprecation_info = {}

    def __new__(mcs, *args, deprecated_in=None, removed_in=None, **kwargs):  # noqa: D102
        return super().__new__(mcs, *args, **kwargs)

    def __init__(cls, name, bases, *args, deprecated_in=None, removed_in=None, **kwargs):
        super().__init__(name, bases, *args, **kwargs)
        if not any(isinstance(b, MigratedClassMeta) for b in bases):
            # First generation
            if len(bases) != 1:
                raise TypeError(f"Migrated Classes must reference precisely one target. "
                                f"{bases} found.")
            if deprecated_in is None or removed_in is None:
                raise TypeError("Migrated Classes must include `deprecated_in` "
                                "and `removed_in` arguments.")
            cls._deprecation_info[cls] = (bases[0], deprecated_in, removed_in)

            def _new(*args_, **kwargs_):
                warn(f"Importing {name} from {cls.__module__} is deprecated as of "
                     f"{deprecated_in} and will be removed in {removed_in}. "
                     f"Please import {bases[0].__name__} from {bases[0].__module__} instead.",
                     DeprecationWarning, stacklevel=2)
                return bases[0](*args_[1:], **kwargs_)

            cls.__new__ = _new

        for base in bases:
            if base in cls._deprecation_info:
                # Second generation
                alias, this_deprecated_in, this_removed_in = cls._deprecation_info[base]
                warn(f"Importing {base.__name__} from {base.__module__} is deprecated as of "
                     f"{this_deprecated_in} and will be removed in {this_removed_in}. "
                     f"Please import {alias.__name__} from {alias.__module__} instead.",
                     DeprecationWarning, stacklevel=2)

    def __instancecheck__(cls, instance):
        return any(cls.__subclasscheck__(c)
                   for c in {type(instance), instance.__class__})

    def __subclasscheck__(cls, subclass):
        try:
            return issubclass(subclass, cls._deprecation_info.get(cls, (type(None), ))[0])
        except RecursionError:
            return False


def generate_shared_meta(target: type):
    """Generate a custom metaclass to avoid method resolution ambiguity."""
    if issubclass(MigratedClassMeta, type(target)):
        return MigratedClassMeta
    else:
        class _CustomMeta(MigratedClassMeta, type(target)):
            pass
        return _CustomMeta


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


def resource_path(*,
                  path_template: str,
                  uid: Optional[Union[UUID, str]] = None,
                  action: Union[str, Sequence[str]] = [],
                  query_terms: Dict[str, str] = {},
                  **kwargs
                  ) -> str:
    """Construct a url from a base path and, optionally, id and/or action."""
    base = urlparse(path_template)
    path = base.path.split('/')

    if uid is not None:
        path.append("{uid}")

    if isinstance(action, str):
        action = [action]
    else:
        action = list(action)
    path.extend(["{}"] * len(action))

    query = urlencode(query_terms)
    new_url = base._replace(path='/'.join(path), query=query).geturl()

    return format_escaped_url(new_url, *action, **kwargs, uid=uid)


def _data_manager_deprecation_checks(session, project_id: UUID, team_id: UUID, obj_type: str):
    if team_id is None:
        if project_id is None:
            raise TypeError("Missing one required argument: team_id.")

        warn(f"{obj_type} now belong to Teams, so the project_id parameter was deprecated in "
             "3.4.0, and will be removed in 4.0. Please provide the team_id instead.",
             DeprecationWarning)
        # avoiding a circular import
        from citrine.resources.project import Project
        team_id = Project.get_team_id_from_project_id(session=session, project_id=project_id)
    return team_id


def _pad_positional_args(args, n):
    if len(args) > 0:
        warn("Positional arguments are deprecated and will be removed in v4.0. Please use keyword "
             "arguments instead.",
             DeprecationWarning)
    return args + (None, ) * (n - len(args))
