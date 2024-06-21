from gemd.entity.object import *
import pytest
from citrine.resources.dataset import Dataset
from gemd.builders.impl import make_node, add_edge
from gemd.util.impl import flatten
from citrine.seeding.find_or_create import find_or_create_team,find_or_create_dataset,find_or_create_project
from gemd.entity.link_by_uid import LinkByUID
from citrine.resources.data_concepts import _make_link_by_uid
from gemd.entity.value import NominalReal


from citrine import Citrine

TESTING_SCOPE = "pne-241-scope"

def seed_registration_no_project(team):
    dataset = find_or_create_dataset(dataset_collection=team.datasets, dataset_name="dataset 1", raise_error=True)
    gemds = []
    for i in range(1,5):
        this_node = make_node(name = f"material {i}", process_name= "fake process")
        this_node.add_uid(scope=TESTING_SCOPE,uid=f"Mat Run {i}")
        this_node.spec.add_uid(scope=TESTING_SCOPE,uid=f"Mat Spec {i}")
        this_node.process.spec.add_uid(scope=TESTING_SCOPE,uid=f"Process Spec {i}")
        this_node.process.add_uid(scope=TESTING_SCOPE,uid=f"Process Run {i}")
        if 1 == i:
            input_mat = this_node
        gemds.extend(flatten(this_node))
    # Make one more complex Material History to ensure get_history works correctly later
    extension = make_node(name = "second material", process_name="second step")
    extension.add_uid(scope=TESTING_SCOPE,uid=f"Mat Run 2-1")
    extension.spec.add_uid(scope=TESTING_SCOPE,uid=f"Mat Spec 2-1")
    extension.process.spec.add_uid(scope=TESTING_SCOPE,uid=f"Process Spec 2-1")
    extension.process.add_uid(scope=TESTING_SCOPE,uid=f"Process Run 2-1")
    gemds.extend(flatten(extension))
    ingreds = add_edge(
        input_material=input_mat,
        output_material=extension,
        mass_fraction=NominalReal(nominal=1,units="")
    )
    ingreds.add_uid(scope=TESTING_SCOPE,id="Ing Run 2-1")
    ingreds.spec.add_uid(scope=TESTING_SCOPE,id="Ing Spec 2-1")
    gemds.extend(flatten(ingreds))

    dataset.delete_contents(prompt_to_confirm=False)
    dataset.register_all(gemds)
    return dataset


def seed_registration_with_project(project):
    with pytest.deprecated_call():
        dataset = find_or_create_dataset(dataset_collection=project.datasets, dataset_name="project dataset 2", raise_error=True)
    gemds = []
    for i in range(6,11):
        this_node = make_node(name = f"material {i}", process_name= "fake process")
        this_node.add_uid(scope=TESTING_SCOPE,uid=f"Mat Run {i}")
        this_node.spec.add_uid(scope=TESTING_SCOPE,uid=f"Mat Spec {i}")
        this_node.process.spec.add_uid(scope=TESTING_SCOPE,uid=f"Process Spec {i}")
        this_node.process.add_uid(scope=TESTING_SCOPE,uid=f"Process Run {i}")
        gemds.extend(flatten(this_node))
    dataset.delete_contents(prompt_to_confirm=False)
    dataset.register_all(gemds)
    dataset_gemd = [x for x in dataset.gemd.list()]
    assert len(dataset_gemd) == 20
    assert len(dataset_gemd) == len([y for y in project.gemd.list()])
    return dataset


def test_registration_and_listing():
    client = Citrine()
    team = find_or_create_team(team_collection=client.teams, team_name="Data Manager Testing Team 1", raise_error=True)
    project = find_or_create_project(project_collection=team.projects, project_name="Project 1", raise_error=True)
    no_p_dataset = seed_registration_no_project(team)
    with_p_dataset = seed_registration_with_project(project)

    assert len([x for x in team.datasets.list()])==2
    assert len(team.owned_dataset_ids())==2
    assert len([x for x in project.datasets.list()])==1
    with pytest.deprecated_call():
        assert len(project.owned_dataset_ids())==2

    assert no_p_dataset.project_id is None
    assert with_p_dataset.project_id == project.uid

    assert len([x for x in no_p_dataset.gemd.list()]) == 20
    mr = no_p_dataset.gemd.get(LinkByUID(scope=TESTING_SCOPE, id="Mat Run 1"))
    assert isinstance(mr, MaterialRun)
    assert mr == team.gemd.get(LinkByUID(scope=TESTING_SCOPE, id="Mat Run 1"))
    mr_link = LinkByUID(scope=TESTING_SCOPE, id="Mat Run 2-1")
    mat_history = no_p_dataset.material_runs.get_history(mr_link)
    assert len(flatten(mat_history)) == 10
    assert len([x for x in no_p_dataset.material_runs.list()]) == 6

    assert len([x for x in with_p_dataset.gemd.list()]) == 26
    assert len([x for x in with_p_dataset.material_runs.list()]) == 6
    assert len([x for x in project.gemd.list()]) == 26
    assert len([x for x in project.material_runs.list()]) == 6
    assert len([x for x in team.gemd.list()]) == 46

def test_sharing():
    client = Citrine()
    team = find_or_create_team(team_collection=client.teams, team_name="Data Manager Testing Team 1", raise_error=True)
    team_2 = find_or_create_team(team_collection=client.teams, team_name="Data Manager Testing Team 2", raise_error=True)
    project = find_or_create_project(project_collection=team.projects, project_name="Project 1", raise_error=True)
    project_2 = find_or_create_project(project_collection=team.projects, project_name="Project 2", raise_error=True)

    no_p_dataset = seed_registration_no_project(team)
    with_p_dataset = seed_registration_with_project(project)

    with pytest.deprecated_call():
        project.publish(resource=with_p_dataset)

    with pytest.deprecated_call():
        project.un_publish(resource=with_p_dataset)

    # Make sure that post Data-Manager Datasets can still be "pulled into" a project for now
    with pytest.deprecated_call():
        project_2.pull_in_resource(resource=no_p_dataset)

    proj_2_dsets = [x for x in project_2.datasets.list()]
    assert len(proj_2_dsets) == 1
    assert len(project_2.owned_dataset_ids()) == 0
    assert len(project.owned_dataset_ids()) == 1
    assert proj_2_dsets[0].uid == no_p_dataset.uid

    assert len([x for x in team_2.datasets.list()]) == 0
    assert len([x for x in team_2.owned_dataset_ids()]) == 0

    team.share(resource=no_p_dataset,target_team_id=team_2.uid)
    assert len([x for x in team_2.datasets.list()]) == 1
    assert len([x for x in team_2.gemd.list()]) == 26
    assert len([x for x in team_2.owned_dataset_ids()]) == 0

    team.share(resource=with_p_dataset,target_team_id=team_2.uid)
    assert len([x for x in team_2.datasets.list()]) == 2
    assert len([x for x in team_2.gemd.list()]) == 46
    assert len([x for x in team_2.owned_dataset_ids()]) == 0
    assert isinstance(team_2.gemd.get(LinkByUID(scope=TESTING_SCOPE, id="Mat Run 1")))

    team.un_share(resource=no_p_dataset,target_team_id=team_2.uid)
    team.un_share(resource=with_p_dataset,target_team_id=team_2.uid)
    assert len([x for x in team_2.datasets.list()]) == 0
    assert len([x for x in team_2.owned_dataset_ids()]) == 0
