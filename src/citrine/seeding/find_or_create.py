from citrine.exceptions import NotFound
from citrine.resources import ProjectCollection
from citrine.resources.dataset import Dataset
from citrine.informatics.workflows.design_workflow import DesignWorkflow
from citrine._rest.collection import CreationType, Collection
from copy import deepcopy


def find_collection(*, collection, name):
    """
    Looks through the pages of a collection for a resource with the specified name.

    Returns it, or if not found, returns None
    """
    if isinstance(collection, ProjectCollection):
        try:
            # try to use search if it is available
            # call list() to collapse the iterator, otherwise the NotFound
            # won't show up until collection_list is used
            collection_list = list(collection.search(search_params={
                "name": {
                    "value": name,
                    "search_method": "EXACT"
                }
            }))
        except (NotFound, NotImplementedError):
            # Search must not be available yet or any more
            collection_list = collection.list()
    else:
        collection_list = collection.list()

    matching_resources = [resource for resource in collection_list if resource.name == name]
    if len(matching_resources) > 1:
        raise ValueError("Found multiple collections with name '{}'".format(name))
    if len(matching_resources) == 1:
        result = matching_resources.pop()
        print('Found existing: {}'.format(result))
        return result
    else:
        return None


def get_by_name_or_create(*, collection, name, default_provider):
    """
    Tries to find a collection by its name (returns first hit).

    If not found, implements default_provider
    """
    found = find_collection(collection=collection, name=name)
    if found:
        return found
    else:
        print('Failed to find resource with name {}, creating one instead.'.format(name))
        return default_provider()


def get_by_name_or_raise_error(*, collection, name):
    """
    Tries to find a collection by its name (returns first hit).

    If not found, raises error
    """
    found = find_collection(collection=collection, name=name)
    if found:
        return found
    else:
        raise ValueError("Did not find resource with the given name: {}".format(name))


def find_or_create_project(*, project_collection, project_name, raise_error=False):
    """
    Tries to find a project by name (returns first hit).

    If not found, creates a new project with the given name
    """
    if raise_error:
        project = get_by_name_or_raise_error(collection=project_collection, name=project_name)
    else:
        project = get_by_name_or_create(
            collection=project_collection,
            name=project_name,
            default_provider=lambda: project_collection.register(project_name)
        )
    return project


def find_or_create_team(*, team_collection, team_name, raise_error=False):
    """
    Tries to find a team by name (returns first hit).

    If not found, creates a new team with the given name
    """
    if raise_error:
        team = get_by_name_or_raise_error(collection=team_collection, name=team_name)
    else:
        team = get_by_name_or_create(
            collection=team_collection,
            name=team_name,
            default_provider=lambda: team_collection.register(team_name)
        )
    return team


def find_or_create_dataset(*, dataset_collection, dataset_name, raise_error=False):
    """
    Tries to find a dataset by name (returns first hit).

    If not found, creates a new dataset with the given name
    """
    if raise_error:
        dataset = get_by_name_or_raise_error(collection=dataset_collection, name=dataset_name)
    else:
        dataset = get_by_name_or_create(
            collection=dataset_collection,
            name=dataset_name,
            default_provider=lambda: dataset_collection.register(
                Dataset(dataset_name, summary="seed summ.", description="seed desc.")
            )
        )
    return dataset


def create_or_update(*, collection: Collection[CreationType], resource: CreationType)\
        -> CreationType:
    """
    Update a resource of a given name belonging to a collection.

    Create it if it doesn't exist. If collection already contains
    a resource with the same name it will be updated. If there are multiple
    resources with the same name it will throw an error.

    Parameters
    ----------
    collection : Collection[CreationType]
        Collection within which you want to update or create a resource
    resource : CreationType
        Resource that you want to create or update.

    Returns
    -------
    CreationType
        Registered updated or created resource.

    """
    old_resource = find_collection(collection=collection, name=resource.name)
    if old_resource:
        print("Updating module: {}".format(resource.name))
        # Copy so that passed-in resource is unaffected
        new_resource = deepcopy(resource)
        new_resource.uid = old_resource.uid
        # Locally created design workflows likely won't have a branch ID but
        # need one to be updated.
        if isinstance(old_resource, DesignWorkflow):
            new_resource.branch_id = old_resource.branch_id
        return collection.update(new_resource)
    else:
        print("Registering new module:  {}".format(resource.name))
        return collection.register(resource)
