from typing import Optional
from uuid import UUID

import pytest
from citrine._rest.collection import Collection
from citrine.resources.dataset import Dataset, DatasetCollection
from citrine.resources.process_spec import ProcessSpecCollection, ProcessSpec
from citrine.resources.project import ProjectCollection, Project
from citrine.seeding.find_or_create import (find_collection, get_by_name_or_create, get_by_name_or_raise_error,
                                            find_or_create_project, find_or_create_dataset)

from tests.utils.session import FakeSession

duplicate_name = "duplicate"


absent_name = "absent"


@pytest.fixture
def fake_collection() -> Collection:
    class FakeCollection(ProcessSpecCollection):
        resources = []

        def register(self, model: ProcessSpec, dry_run=False) -> ProcessSpec:
            self.resources.append(model)
            return model

        def list(self, page: Optional[int] = None, per_page: int = 100):
            if page is None:
                return self.resources
            else:
                return self.resources[(page - 1)*per_page:page*per_page]

    collection = FakeCollection(UUID('6b608f78-e341-422c-8076-35adc8828545'),
                                UUID('6b608f78-e341-422c-8076-35adc8828545'),
                                session)
    for i in range(0, 5):
        collection.register(ProcessSpec("resource " + str(i)))
    for i in range(0, 2):
        collection.register(ProcessSpec(duplicate_name))
    return collection


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project_collection() -> ProjectCollection:
    class SeedingTestProjectCollection(ProjectCollection):
        projects = []

        def register(self, name: str, description: Optional[str] = None) -> Project:
            project = Project(name=name)
            self.projects.append(project)
            return project

        def list(self, page: Optional[int] = None, per_page: int = 100):
            if page is None:
                return self.projects
            else:
                return self.projects[(page - 1)*per_page:page*per_page]

        def delete(self, uuid):
            raise NotImplementedError

    projects = SeedingTestProjectCollection()
    for i in range(0, 5):
        projects.register("project " + str(i))
    for i in range(0, 2):
        projects.register(duplicate_name)
    return projects


@pytest.fixture
def dataset_collection() -> DatasetCollection:
    class SeedingTestDatasetCollection(DatasetCollection):
        datasets = []

        def register(self, model: Dataset) -> Dataset:
            self.datasets.append(model)
            return model

        def list(self, page: Optional[int] = None, per_page: int = 100):
            if page is None:
                return self.datasets
            else:
                return self.datasets[(page - 1)*per_page:page*per_page]

    datasets = SeedingTestDatasetCollection(UUID('6b608f78-e341-422c-8076-35adc8828545'), session)
    for i in range(0, 5):
        num_string = str(i)
        datasets.register(Dataset("dataset " + num_string, "summ " + num_string, "desc " + num_string))
    for i in range(0, 2):
        datasets.register(Dataset(duplicate_name, "dup", "duplicate"))
    return datasets


def test_find_collection_no_exist(session, fake_collection):
    # test result when resource doesn't exist
    result = find_collection(fake_collection, absent_name)
    assert result is None


def test_find_collection_exist(fake_collection):
    # test result when resource exists
    result = find_collection(fake_collection, "resource 1")
    assert result.name == "resource 1"


def test_find_collection_exist_multiple(fake_collection):
    # test result when resource exists multiple times
    with pytest.raises(ValueError):
        find_collection(fake_collection, duplicate_name)


def test_get_by_name_or_create_no_exist(fake_collection):
    # test when name doesn't exist
    default_provider = lambda: fake_collection.register(ProcessSpec("New Resource"))
    old_resource_count = len(list(fake_collection.list()))
    result = get_by_name_or_create(fake_collection, "New Resource", default_provider)
    new_resource_count = len(list(fake_collection.list()))
    assert result.name == "New Resource"
    assert new_resource_count == old_resource_count + 1


def test_get_by_name_or_create_exist(fake_collection):
    # test when name exists
    resource_name = "resource 2"
    default_provider = lambda: fake_collection.register(ProcessSpec("New Resource"))
    old_resource_count = len(list(fake_collection.list()))
    result = get_by_name_or_create(fake_collection, resource_name, default_provider)
    new_resource_count = len(list(fake_collection.list()))
    assert result.name == resource_name
    assert new_resource_count == old_resource_count


def test_get_by_name_or_raise_error_no_exist(fake_collection):
    # test when name doesn't exist
    with pytest.raises(ValueError):
        get_by_name_or_raise_error(fake_collection, "New Resource")


def test_get_by_name_or_raise_error_exist(fake_collection):
    # test when name exists
    result = get_by_name_or_raise_error(fake_collection, "resource 2")
    assert result.name == "resource 2"


def test_find_or_create_project_no_exist(project_collection):
    # test when project doesn't exist
    old_project_count = len(list(project_collection.list()))
    result = find_or_create_project(project_collection, absent_name)
    new_project_count = len(list(project_collection.list()))
    assert result.name == absent_name
    assert new_project_count == old_project_count + 1


def test_find_or_create_project_exist(project_collection):
    # test when project exists
    old_project_count = len(list(project_collection.list()))
    result = find_or_create_project(project_collection, "project 2")
    new_project_count = len(list(project_collection.list()))
    assert result.name == "project 2"
    assert new_project_count == old_project_count


def test_find_or_create_project_exist_multiple(project_collection):
    # test when project exists multiple times
    with pytest.raises(ValueError):
        find_or_create_project(project_collection, duplicate_name)


def test_find_or_create_raise_error_project_no_exist(project_collection):
    # test when project doesn't exist and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_project(project_collection, absent_name, raise_error=True)


def test_find_or_create_raise_error_project_exist(project_collection):
    # test when project exists and raise_error flag is on
    old_project_count = len(list(project_collection.list()))
    result = find_or_create_project(project_collection, "project 3", raise_error=True)
    new_project_count = len(list(project_collection.list()))
    assert result.name == "project 3"
    assert new_project_count == old_project_count


def test_find_or_create_raise_error_project_exist_multiple(project_collection):
    # test when project exists multiple times and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_project(project_collection, duplicate_name, raise_error=True)


def test_find_or_create_dataset_no_exist(dataset_collection):
    # test when dataset doesn't exist
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection, absent_name)
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == absent_name
    assert new_dataset_count == old_dataset_count + 1


def test_find_or_create_dataset_exist(dataset_collection):
    # test when dataset exists
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection, "dataset 2")
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == "dataset 2"
    assert new_dataset_count == old_dataset_count


def test_find_or_create_dataset_exist_multiple(dataset_collection):
    # test when dataset exists multiple times
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection, duplicate_name)


def test_find_or_create_dataset_raise_error_no_exist(dataset_collection):
    # test when dataset doesn't exist and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection, absent_name, raise_error=True)


def test_find_or_create_dataset_raise_error_exist(dataset_collection):
    # test when dataset exists and raise_error flag is on
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection, "dataset 3", raise_error=True)
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == "dataset 3"
    assert new_dataset_count == old_dataset_count


def test_find_or_create_dataset_raise_error_exist_multiple(dataset_collection):
    # test when dataset exists multiple times and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection, duplicate_name, raise_error=True)
