from typing import Callable, Optional, Union
from uuid import UUID, uuid4

import pytest
from citrine._rest.collection import Collection
from citrine.resources.dataset import Dataset, DatasetCollection
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine.resources.process_spec import ProcessSpecCollection, ProcessSpec
from citrine.resources.predictor import PredictorCollection
from citrine.resources.project import ProjectCollection
from citrine.resources.team import TeamCollection
from citrine.informatics.predictors import AutoMLPredictor, GraphPredictor
from citrine.seeding.find_or_create import (find_collection, get_by_name_or_create,
                                            get_by_name_or_raise_error,
                                            find_or_create_project, find_or_create_dataset,
                                            create_or_update, find_or_create_team)
from tests.utils.factories import BranchDataFactory, DesignWorkflowDataFactory
from tests.utils.fakes.fake_dataset_collection import FakeDatasetCollection
from tests.utils.fakes import FakePredictorCollection
from tests.utils.fakes.fake_project_collection import FakeProjectCollection
from tests.utils.fakes.fake_team_collection import FakeTeamCollection

from tests.utils.session import FakeSession

duplicate_name = "duplicate"


absent_name = "absent"


# With our testing, it's important that the same session instance is carried throughout. When we
# have code which does a deep copy of a module (such as create_or_update), the session from that
# module will be a different object, which can cause issues.
class LocalDesignWorkflowCollection(DesignWorkflowCollection):
    def update(self, model):
        model._session = self.session
        return super().update(model)


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

    collection = FakeCollection(dataset_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
                                team_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
                                session=FakeSession())
    for i in range(0, 5):
        collection.register(ProcessSpec("resource " + str(i)))
    for i in range(0, 2):
        collection.register(ProcessSpec(duplicate_name))
    return collection


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project_collection() -> Callable[[bool], ProjectCollection]:

    def _make_project(search_implemented: bool = True, team_id: Optional[Union[UUID, str]] = uuid4()):
        projects = FakeProjectCollection(search_implemented, team_id)
        for i in range(0, 5):
            projects.register("project " + str(i))
        for i in range(0, 2):
            projects.register(duplicate_name)
        return projects

    return _make_project


@pytest.fixture
def team_collection() -> Callable[[bool], TeamCollection]:

    def _make_team():
        teams = FakeTeamCollection(True)
        for i in range(0, 5):
            teams.register("team " + str(i))
        for i in range(0, 2):
            teams.register(duplicate_name)
        return teams

    return _make_team


@pytest.fixture
def dataset_collection() -> DatasetCollection:
    datasets = FakeDatasetCollection(team_id=UUID('6b608f78-e341-422c-8076-35adc8828545'), session=FakeSession())
    for i in range(0, 5):
        num_string = str(i)
        datasets.register(Dataset("dataset " + num_string, summary="summ " + num_string, description="desc " + num_string))
    for i in range(0, 2):
        datasets.register(Dataset(duplicate_name, summary="dup", description="duplicate"))
    return datasets

@pytest.fixture
def predictor_collection() -> PredictorCollection:
    predictors = FakePredictorCollection(UUID('6b608f78-e341-422c-8076-35adc8828545'), FakeSession())

    # Adding a few predictors in the collection to have something to update
    for i in range(0, 5):
        pred = GraphPredictor(
            name=f"resource {i}",
            description="",
            predictors=[AutoMLPredictor(name="", description="", inputs=[], outputs=[])]
        )
        predictors.register(pred)

    # Adding a few predictors with the same name ("resource {0,1}" were made above)
    # this is used to test behavior if there are duplicates
    for i in range(0, 2):
        pred = GraphPredictor(
            name=f"resource {i}",
            description="",
            predictors=[AutoMLPredictor(name="", description="", inputs=[], outputs=[])]
        )
        predictors.register(pred)
    return predictors


def test_find_collection_no_exist(session, fake_collection):
    # test result when resource doesn't exist
    result = find_collection(collection=fake_collection, name=absent_name)
    assert result is None


def test_find_collection_exist(fake_collection):
    # test result when resource exists
    result = find_collection(collection=fake_collection, name="resource 1")
    assert result.name == "resource 1"


def test_find_collection_exist_multiple(fake_collection):
    # test result when resource exists multiple times
    with pytest.raises(ValueError):
        find_collection(collection=fake_collection, name=duplicate_name)


def test_get_by_name_or_create_no_exist(fake_collection):
    # test when name doesn't exist
    default_provider = lambda: fake_collection.register(ProcessSpec("New Resource"))
    old_resource_count = len(list(fake_collection.list()))
    result = get_by_name_or_create(collection=fake_collection, name="New Resource", default_provider=default_provider)
    new_resource_count = len(list(fake_collection.list()))
    assert result.name == "New Resource"
    assert new_resource_count == old_resource_count + 1


def test_get_by_name_or_create_exist(fake_collection):
    # test when name exists
    resource_name = "resource 2"
    default_provider = lambda: fake_collection.register(ProcessSpec("New Resource"))
    old_resource_count = len(list(fake_collection.list()))
    result = get_by_name_or_create(collection=fake_collection, name=resource_name, default_provider=default_provider)
    new_resource_count = len(list(fake_collection.list()))
    assert result.name == resource_name
    assert new_resource_count == old_resource_count


def test_get_by_name_or_raise_error_no_exist(fake_collection):
    # test when name doesn't exist
    with pytest.raises(ValueError):
        get_by_name_or_raise_error(collection=fake_collection, name="New Resource")


def test_get_by_name_or_raise_error_exist(fake_collection):
    # test when name exists
    result = get_by_name_or_raise_error(collection=fake_collection, name="resource 2")
    assert result.name == "resource 2"


def test_find_or_create_team_no_exist(team_collection):
    # test when team doesn't exist
    collection = team_collection()
    old_team_count = len(list(collection.list()))
    result = find_or_create_team(team_collection=collection, team_name=absent_name)
    new_team_count = len(list(collection.list()))
    assert result.name == absent_name
    assert new_team_count == old_team_count + 1


def test_find_or_create_team_exist(team_collection):
    # test when team exists
    collection = team_collection()
    old_team_count = len(list(collection.list()))
    result = find_or_create_team(team_collection=collection, team_name="team 2")
    new_team_count = len(list(collection.list()))
    assert result.name == "team 2"
    assert new_team_count == old_team_count


def test_find_or_create_raise_error_team_no_exist(team_collection):
    # test when team doesn't exist and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_team(team_collection=team_collection(), team_name=absent_name, raise_error=True)


def test_find_or_create_project_no_exist(project_collection):
    # test when project doesn't exist
    collection = project_collection()
    old_project_count = len(list(collection.list()))
    result = find_or_create_project(project_collection=collection, project_name=absent_name)
    new_project_count = len(list(collection.list()))
    assert result.name == absent_name
    assert new_project_count == old_project_count + 1


def test_find_or_create_project_exist(project_collection):
    # test when project exists
    collection = project_collection()
    old_project_count = len(list(collection.list()))
    result = find_or_create_project(project_collection=collection, project_name="project 2")
    new_project_count = len(list(collection.list()))
    assert result.name == "project 2"
    assert new_project_count == old_project_count


def test_find_or_create_project_exist_no_search(project_collection):
    # test when project exists
    collection = project_collection(False)
    old_project_count = len(list(collection.list()))
    result = find_or_create_project(project_collection=collection, project_name="project 2")
    new_project_count = len(list(collection.list()))
    assert result.name == "project 2"
    assert new_project_count == old_project_count


def test_find_or_create_project_exist_multiple(project_collection):
    # test when project exists multiple times
    with pytest.raises(ValueError):
        find_or_create_project(project_collection=project_collection(), project_name=duplicate_name)


def test_find_or_create_raise_error_project_no_exist(project_collection):
    # test when project doesn't exist and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_project(project_collection=project_collection(), project_name=absent_name, raise_error=True)


def test_find_or_create_raise_error_project_exist(project_collection):
    # test when project exists and raise_error flag is on
    collection = project_collection()
    old_project_count = len(list(collection.list()))
    result = find_or_create_project(project_collection=collection, project_name="project 3", raise_error=True)
    new_project_count = len(list(collection.list()))
    assert result.name == "project 3"
    assert new_project_count == old_project_count


def test_find_or_create_raise_error_project_exist_multiple(project_collection):
    # test when project exists multiple times and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_project(project_collection=project_collection(), project_name=duplicate_name, raise_error=True)


def test_find_or_create_project_no_team(project_collection):
    # test when project collection has no team
    collection = project_collection(team_id=None)
    with pytest.raises(NotImplementedError):
        find_or_create_project(project_collection=collection, project_name="project 2")


def test_find_or_create_dataset_no_exist(dataset_collection):
    # test when dataset doesn't exist
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection=dataset_collection, dataset_name=absent_name)
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == absent_name
    assert new_dataset_count == old_dataset_count + 1


def test_find_or_create_dataset_exist(dataset_collection):
    # test when dataset exists
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection=dataset_collection, dataset_name="dataset 2")
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == "dataset 2"
    assert new_dataset_count == old_dataset_count


def test_find_or_create_dataset_exist_multiple(dataset_collection):
    # test when dataset exists multiple times
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection=dataset_collection, dataset_name=duplicate_name)


def test_find_or_create_dataset_raise_error_no_exist(dataset_collection):
    # test when dataset doesn't exist and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection=dataset_collection, dataset_name=absent_name, raise_error=True)


def test_find_or_create_dataset_raise_error_exist(dataset_collection):
    # test when dataset exists and raise_error flag is on
    old_dataset_count = len(list(dataset_collection.list()))
    result = find_or_create_dataset(dataset_collection=dataset_collection, dataset_name="dataset 3", raise_error=True)
    new_dataset_count = len(list(dataset_collection.list()))
    assert result.name == "dataset 3"
    assert new_dataset_count == old_dataset_count


def test_find_or_create_dataset_raise_error_exist_multiple(dataset_collection):
    # test when dataset exists multiple times and raise_error flag is on
    with pytest.raises(ValueError):
        find_or_create_dataset(dataset_collection=dataset_collection, dataset_name=duplicate_name, raise_error=True)


def test_create_or_update_none_found(predictor_collection):
    # test when resource doesn't exist with listed name and check if new one is created
    assert not [r for r in list(predictor_collection.list()) if r.name == absent_name]
    aml = AutoMLPredictor(name=absent_name, description='', inputs=[], outputs=[])
    pred = GraphPredictor(name=absent_name, description='', predictors=[aml])
    #verify that the returned object is updated
    returned_pred = create_or_update(collection=predictor_collection, resource=pred)
    assert returned_pred.uid == pred.uid
    assert returned_pred.name == pred.name
    assert returned_pred.description == pred.description
    #verify that the collection is also updated
    assert any([r for r in list(predictor_collection.list()) if r.name == absent_name])


def test_create_or_update_unique_found(predictor_collection):
    # test when there is a single unique resource that exists with the listed name and update
    aml = AutoMLPredictor(name="", description='', inputs=[], outputs=[])
    pred = GraphPredictor(name="resource 4", description="I am updated!", predictors=[aml])
    #verify that the returned object is updated
    returned_pred = create_or_update(collection=predictor_collection, resource=pred)
    assert returned_pred.name == pred.name
    assert returned_pred.description == pred.description
    #verify that the collection is also updated
    updated_pred = [r for r in list(predictor_collection.list()) if r.name == "resource 4"][0]
    assert updated_pred.description == "I am updated!"


def test_create_or_update_unique_found_design_workflow(session):
    # test when there is a single unique resource that exists with the listed name and update
    branch_data = BranchDataFactory()
    root_id = UUID(branch_data["metadata"]["root_id"])
    version = branch_data["metadata"]["version"]
    dw1_dict = DesignWorkflowDataFactory(register=True)
    dw2_dict = DesignWorkflowDataFactory(register=True, branch=branch_data)
    dw3_dict = DesignWorkflowDataFactory(register=True)
    session.set_responses(
        # List
        {"response": [dw1_dict, dw2_dict, dw3_dict]},  # Return the design workflows
        # Update
        {"response": []},  # Check if there are any executions
        dw2_dict,  # Return the updated design workflow
    )

    collection = LocalDesignWorkflowCollection(project_id=uuid4(), session=session, branch_root_id=root_id, branch_version=version)
    dw2 = collection.build(dw2_dict)

    #verify that the returned object is updated
    returned_dw = create_or_update(collection=collection, resource=dw2)

    assert returned_dw.name == dw2.name
    assert returned_dw.branch_root_id == collection.branch_root_id == UUID(branch_data["metadata"]["root_id"])
    assert returned_dw.branch_version == collection.branch_version == branch_data["metadata"]["version"]

def test_create_or_update_raise_error_multiple_found(predictor_collection):
    # test when there are multiple resources that exists with the same listed name and raise error
    # resource 1 is not a unique name
    aml = AutoMLPredictor(name="", description='', inputs=[], outputs=[])
    pred = GraphPredictor(name="resource 1", description="I am updated!", predictors=[aml])
    with pytest.raises(ValueError):
        create_or_update(collection=predictor_collection, resource=pred)
