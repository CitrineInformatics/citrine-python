# This contains factories for creating test input, using factory boy
# https://factoryboy.readthedocs.io/en/latest/index.html

# Naming convention here is to use "*DataFactory" for dictionaries used as API input/out, and
# <ModelName>Factory for the domain objects themselves

from random import randrange, random

import factory
from citrine.informatics.scores import LIScore
from citrine.resources.dataset import Dataset
from citrine.resources.file_link import _Uploader
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.process_template import ProcessTemplate
from gemd.entity.link_by_uid import LinkByUID


class WithIdDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')


class TeamDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    created_at = None


class ProjectDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    status = 'CREATED'
    created_at = None


class DataVersionUpdateFactory(factory.DictFactory):
    current = "gemd::48e5e2f3-d447-458b-a8ea-d9cdb782b86e::1"
    latest = "gemd::48e5e2f3-d447-458b-a8ea-d9cdb782b86e::2"


class PredictorRefFactory(factory.DictFactory):
    predictor_id = factory.Faker('uuid4')
    predictor_version = randrange(10)


class BranchDataUpdateFactory(factory.DictFactory):
    data_updates = [DataVersionUpdateFactory()]
    predictors = [PredictorRefFactory()]


class NextBranchVersionFactory(factory.DictFactory):
    data_updates = [DataVersionUpdateFactory()]
    predictors = [PredictorRefFactory()]


class BranchDataFieldFactory(factory.DictFactory):
    name = factory.Faker('company')


class BranchMetadataFieldFactory(factory.DictFactory):
    root_id = factory.Faker('uuid4')
    archived = factory.Faker('boolean')
    version = randrange(10)
    created = None
    updated = None


class BranchDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(BranchDataFieldFactory)
    metadata = factory.SubFactory(BranchMetadataFieldFactory)


class UserDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    screen_name = factory.Faker('name')
    position = factory.Faker('job')
    email = factory.Faker('email')
    is_admin = factory.Faker('boolean')


class GemTableDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    version = randrange(10)
    signed_download_url = factory.Faker('uri')


class ListGemTableVersionsDataFactory(factory.DictFactory):
    tables = [GemTableDataFactory(), GemTableDataFactory(), GemTableDataFactory()]
    # Explicitly set version numbers so that they are distinct
    tables[0]["version"] = 1
    tables[1]["version"] = 4
    tables[2]["version"] = 2


class TableConfigJSONDataFactory(factory.DictFactory):
    """ This is simply the JSON Blob stored in an Table Config Version"""
    name = factory.Faker("company")
    description = factory.Faker('bs')
    rows = []
    columns = []
    variables = []
    datasets = []


class TableConfigVersionJSONDataFactory(factory.DictFactory):
    ara_definition = factory.SubFactory(TableConfigJSONDataFactory)
    id = factory.Faker('uuid4')
    version_number = randrange(10)


class TableConfigResponseDataFactory(factory.DictFactory):
    """This is the TableConfig object that encapsulates both version and definition info from the server"""
    definition = factory.SubFactory(WithIdDataFactory)
    version = factory.SubFactory(TableConfigVersionJSONDataFactory)


class ListTableConfigResponseDataFactory(factory.DictFactory):
    """This encapsulates all of the versions of a table config object."""
    definition = factory.SubFactory(WithIdDataFactory)
    versions = [TableConfigVersionJSONDataFactory(), TableConfigVersionJSONDataFactory(), TableConfigVersionJSONDataFactory()]
    # Explicitly set version numbers so that they are distinct
    versions[0]['version_number'] = 1
    versions[1]['version_number'] = 4
    versions[2]['version_number'] = 2


class TableDataSourceDataFactory(factory.DictFactory):
    type = "hosted_table_data_source"
    table_id = factory.Faker("uuid4")
    table_version = randrange(10)
    formulation_descriptor = None


class UserTimestampDataFactory(factory.DictFactory):
    user = factory.Faker("uuid4")
    time = factory.Faker("iso8601")


class StatusDataFactory(factory.DictFactory):
    name = "READY"
    info = []
    detail = []


class PredictorMetadataDataFactory(factory.DictFactory):
    status = factory.SubFactory(StatusDataFactory)
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)
    version = 1
    draft = True


class PredictorInstanceDataFactory(factory.DictFactory):
    name = factory.Faker("company")
    description = factory.Faker("catch_phrase")
    predictors = []
    training_data = factory.List([factory.SubFactory(TableDataSourceDataFactory)])
    type = "Graph"


# The name isn't a typo. The class is a factory (which uses the suffix "DataFactory") for the
# predictor data object.
class PredictorDataDataFactory(factory.DictFactory):
    name = factory.LazyAttribute(lambda data: data.instance["name"])
    description = factory.LazyAttribute(lambda data: data.instance["description"])
    instance = factory.SubFactory(PredictorInstanceDataFactory)


class PredictorEntityDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(PredictorDataDataFactory)
    metadata = factory.SubFactory(PredictorMetadataDataFactory)


class PredictorEvaluationWorkflowDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker("company")
    description = factory.Faker("catch_phrase")
    archived = False
    evaluators = []
    type = "PredictorEvaluationWorkflow"
    status = "SUCCEEDED"
    status_description = "READY"
    status_detail = []


class DesignSpaceConfigDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker("company")
    descriptor = factory.Faker("catch_phrase")
    subspaces = []
    dimensions = []
    type = "ProductDesignSpace"


class DesignSpaceDataFactory(factory.DictFactory):
    config = factory.SubFactory(DesignSpaceConfigDataFactory)
    id = factory.Faker('uuid4')
    display_name = factory.Faker("company")
    archived = False
    module_type = "DESIGN_SPACE"
    status = "READY"
    status_detail = []


class DesignWorkflowDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker("company")
    description = factory.Faker("catch_phrase")
    archived = False
    design_space_id = factory.Faker("uuid4")
    predictor_id = factory.Faker("uuid4")
    status = "SUCCEEDED"
    status_description = "READY"
    status_detail = []


class JobSubmissionResponseFactory(factory.DictFactory):
    job_id = factory.Faker('uuid4')


class DatasetDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')
    deleted = False
    created_by = factory.Faker('uuid4')
    updated_by = factory.Faker('uuid4')
    deleted_by = factory.Faker('uuid4')
    unique_name = None
    create_time = None
    update_time = None
    delete_time = None
    public = False


class IDDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')


class LinkByUIDInputFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    type = 'link_by_uid'
    scope = 'id'


class FileLinkDataFactory(factory.DictFactory):
    url = factory.Faker('uri')
    filename = factory.Faker('file_name')
    type = 'file_link'


class MaterialRunDataFactory(factory.DictFactory):
    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = ["color"]
    notes = None
    process = factory.SubFactory(LinkByUIDInputFactory)
    sample_type = 'experimental'
    spec = None
    file_links = []
    type = 'material_run'


class LinkByUIDFactory(factory.Factory):
    class Meta:
        model = LinkByUID

    scope = 'id'
    id = factory.Faker('uuid4')


class MaterialRunFactory(factory.Factory):
    class Meta:
        model = MaterialRun

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    notes = None
    process = factory.SubFactory(LinkByUIDFactory)
    sample_type = 'experimental'
    spec = None
    file_links = []


class DatasetFactory(factory.Factory):
    class Meta:
        model = Dataset

    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')
    unique_name = None


class _UploaderFactory(factory.Factory):
    class Meta:
        model = _Uploader

    @factory.post_generation
    def assign_values(obj, create, extracted):
        obj.bucket = 'citrine-datasvc'
        obj.object_key = '334455'
        obj.upload_id = 'dea3a-555'
        obj.region_name = 'us-west'
        obj.aws_access_key_id = 'dkfjiejkcm'
        obj.aws_secret_access_key = 'ifeemkdsfjeijie8759235u2wjr388'
        obj.aws_session_token = 'fafjeijfi87834j87woa'
        obj.s3_version = '2'


class MLIScoreFactory(factory.Factory):
    class Meta:
        model = LIScore

    baselines = []
    objectives = []
    constraints = []


class MaterialSpecFactory(factory.Factory):
    class Meta:
        model = MaterialSpec

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    notes = None
    process = factory.SubFactory(LinkByUIDFactory)
    file_links = []
    template = None
    properties = []


class MaterialTemplateFactory(factory.Factory):
    class Meta:
        model = MaterialTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    properties = []
    description = factory.Faker('catch_phrase')


class MaterialSpecDataFactory(factory.DictFactory):
    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = ["color"]
    notes = None
    process = factory.SubFactory(LinkByUIDInputFactory)
    template = None
    file_links = []
    type = 'material_spec'


class ProcessTemplateFactory(factory.Factory):
    class Meta:
        model = ProcessTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    description = factory.Faker('catch_phrase')
    conditions = []
    parameters = []


class ExperimentDataSourceDataDataFactory(factory.DictFactory):
    experiments = []


class ExperimentDataSourceMetadataDataFactory(factory.DictFactory):
    branch_root_id = factory.Faker('uuid4')
    version = randrange(1, 10)
    created = factory.SubFactory(UserTimestampDataFactory)


class ExperimentDataSourceDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(ExperimentDataSourceDataDataFactory)
    metadata = factory.SubFactory(ExperimentDataSourceMetadataDataFactory)

    def __init__(*, experiments=[], **kwargs):
        kwargs.pop("data", None)
        data = ExperimentDataSourceDataDataFactory(experiments=experiments)

        print(data)

        super().__init__(data=data, **kwargs)


class CandidateExperimentSnapshotDataFactory(factory.DictFactory):
    experiment_id = factory.Faker('uuid4')
    candidate_id = factory.Faker('uuid4')
    workflow_id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('company')
    updated_time = factory.Faker("iso8601")

    overrides = {}


class CategoricalExperimentValueDataFactory(factory.DictFactory):
    type = "CategoricalValue"
    value = factory.Faker('company')


class ChemicalFormulaExperimentValueDataFactory(factory.DictFactory):
    type = "OrganicValue"
    value = factory.Faker('company')


class IntegerExperimentValueDataFactory(factory.DictFactory):
    type = "IntegerValue"
    value = randrange(1, 100)


class MixtureExperimentValueDataFactory(factory.DictFactory):
    type = "MixtureValue"
    value = {}


class MolecularStructureExperimentValueDataFactory(factory.DictFactory):
    type = "InorganicValue"
    value = factory.Faker('company')


class RealExperimentValueDataFactory(factory.DictFactory):
    type = "RealValue"
    value = randrange(1, 100) * random()
