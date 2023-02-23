import os
from citrine import Citrine
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.seeding.find_or_create import find_or_create_project, find_or_create_dataset, find_or_create_team

from gemd.builders.impl import make_node
from gemd.util import flatten

# token request
# export CITRINE_LOCAL_API_KEY=$(curl -s -H "Content-Type: application/json" localhost:8402/api/v1/tokens/generate -X POST -d '{"email": "fe-admin@citrine.io", "scopes": ["modules"]}' | jq -r .refresh_token)

if __name__ == "__main__":
    client = Citrine(scheme="http", host="localhost", port="8402", api_key=os.environ["CITRINE_LOCAL_API_KEY"])
    # client = Citrine(scheme="https", host='development.citrine-platform.com', port='443', api_key=os.environ["CITRINE_DEV_API_KEY"])

# If you need to interact with S3, you'll need to modify a few variables on the
# session object.
#     client.session.s3_endpoint_url = "http://localhost:9572"
#     client.session.s3_use_ssl = False
#     client.session.s3_addressing_style = "path"

    team = find_or_create_team(team_name="team", team_collection=client.teams)
    project = find_or_create_project(project_collection=team.projects, project_name="project")
    dataset = find_or_create_dataset(dataset_collection=project.datasets, dataset_name="dataset")


    proc_template = ProcessTemplate(name="pt")
    mat_template = MaterialTemplate(name="matt")

    cust_id = "density"

    mat_run = make_node(name="matr", process_template=proc_template, material_template=mat_template)
    mat_run.uids["some_scope"] = cust_id
    stuff = flatten(mat_run, scope="whatever")

    dataset.register_all(stuff)

    # res = project.list_by_id("density") # FIXME not wired up in shire yet
    res = project.material_runs.list_by_id("density")
    # res = dataset.material_runs.list_by_name("matr")

    res = client.session.get_resource(f"/projects/{project.uid}/material-runs/density/search-by-id")


    print([i for i in res])




