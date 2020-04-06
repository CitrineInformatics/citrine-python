from citrine.resources.dataset import Dataset


def find_collection(collection, name):
    """
    Looks through the pages of a collection for a resource with the specified name.

    Returns it, or if not found, returns None
    """
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


def get_by_name_or_create(collection, name, default_provider):
    """
    Tries to find a collection by its name (returns first hit).

    If not found, implements default_provider
    """
    found = find_collection(collection, name)
    if found:
        return found
    else:
        print('Failed to find resource with name {}, creating one instead.'.format(name))
        return default_provider()


def get_by_name_or_raise_error(collection, name):
    """
    Tries to find a collection by its name (returns first hit).

    If not found, raises error
    """
    found = find_collection(collection, name)
    if found:
        return found
    else:
        raise ValueError("Did not find resource with the given name: {}".format(name))


def find_or_create_project(project_collection, project_name, raise_error=False):
    """
    Tries to find a project by name (returns first hit).

    If not found, creates a new project with the given name
    """
    if raise_error:
        project = get_by_name_or_raise_error(project_collection, project_name)
    else:
        def default_provider():
            return project_collection.register(project_name)
        project = get_by_name_or_create(project_collection, project_name, default_provider)
    return project


def find_or_create_dataset(dataset_collection, dataset_name, raise_error=False):
    """
    Tries to find a dataset by name (returns first hit).

    If not found, creates a new dataset with the given name
    """
    if raise_error:
        dataset = get_by_name_or_raise_error(dataset_collection, dataset_name)
    else:
        def default_provider():
            return dataset_collection.register(Dataset(dataset_name, "seed summ.", "seed desc."))
        dataset = get_by_name_or_create(dataset_collection, dataset_name, default_provider)
    return dataset
