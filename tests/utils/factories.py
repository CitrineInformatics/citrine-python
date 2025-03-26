# This contains factories for creating test input, using factory boy
# https://factoryboy.readthedocs.io/en/latest/index.html

# Naming convention here is to use "*DataFactory" for dictionaries used as API input/out, and
# <ModelName>Factory for the domain objects themselves

import arrow
import factory
from faker.providers.date_time import Provider
from random import random, randint
from typing import Set, Optional

from citrine.gemd_queries.gemd_query import *
from citrine.gemd_queries.criteria import *
from citrine.gemd_queries.filter import *
from citrine.informatics.scores import LIScore
from citrine.informatics.workflows import DesignWorkflow
from citrine.jobs.job import JobStatus
from citrine.resources.dataset import Dataset
from citrine.resources.file_link import _Uploader
from citrine.resources.ingestion import IngestionStatusType
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.table_config import TableConfigInitiator

from gemd import LinkByUID, EmpiricalFormula, FileLink
from gemd.enumeration import SampleType


class AugmentedProvider(Provider):
    def random_formula(self, count: int = None, elements: Set[str] = None) -> str:
        """Generate a random, well-formed chemical formula.  Likely non-physical."""
        if not elements:  # None or empty
            elements = list(EmpiricalFormula.all_elements())  # Must be Sequence
        if count is None:
            count = self.generator.random.randrange(1, 5)
        components = sorted(self.generator.random.sample(elements, count))
        # Use weights to bias toward looking more real-ish
        amounts = self.generator.random.choices([1, 2, 3, 4, 5], weights=[40, 40, 10, 10, 2], k=count)
        return "".join(f"({c}){a}" for c, a in zip(components, amounts))

    def random_smiles(self) -> str:
        """Generate a random, well-formed chemical formula.  Likely non-physical."""
        element_weights = {  # With selection weights
            "C": 100,
            "O": 20,
            "N": 20,
            "P": 2,
            "S": 2,
            "B": 2,
            "F": 1,
            "Cl": 1,
            "Br": 1,
            "I": 1
        }
        valence = {
            "B": 3,
            "C": 4,
            "N": 3,
            "O": 2,
            "P": 3,
            "S": 4,
            "F": 1,
            "Cl": 1,
            "Br": 1,
            "I": 1
        }
        bonds = ['', '=', '#', '$']

        elements = list(element_weights)
        weights = list(element_weights.values())

        smiles = self.generator.random.choices(elements, weights=weights)[0]
        remain = [valence[smiles[0]]]
        while not remain:
            die = self.generator.random.randrange(100 - len(smiles)) // 3 ** len(remain)
            if remain[-1] == 0 or die == 0:
                # Drop a layer
                remain.pop()
                smiles += ")"
            else:
                atom = self.generator.random.choices(elements, weights=weights)[0]
                max_bond = max(valence[atom], remain[-1])
                bond = 1 + self.generator.random.choices(
                    range(max_bond),
                    weights=[0.1 ** i for i in range(max_bond)]
                )[0]
                remain[-1] -= bond
                if remain[-1] > 1 and self.generator.random.randrange(3 ** len(remain)) == 0:
                    # Branch
                    remain.append(None)
                    smiles += "("
                remain[-1] = valence[atom] - bond
                smiles += f"{bonds[bond - 1]}{atom}"

        return smiles[:-1]  # Always has a superfluous ) at the end

    def unix_milliseconds(
            self,
            end_milliseconds: Optional[int] = None,
            start_milliseconds: Optional[int] = None,
    ) -> float:
        """
        Get a timestamp in milliseconds between January 1, 1970 and now, unless
        passed explicit start_datetime or end_datetime values.

        :example: 1061306726600
        """
        if start_milliseconds is not None:
            start_datetime = arrow.get(start_milliseconds / 1000).datetime
        else:
            start_datetime = None

        if end_milliseconds is not None:
            end_datetime = arrow.get(end_milliseconds / 1000).datetime
        else:
            end_datetime = None

        epoch = self.unix_time(end_datetime=end_datetime, start_datetime=start_datetime)
        return int(1000 * epoch)


factory.Faker.add_provider(AugmentedProvider)


class UserTimestampDataFactory(factory.DictFactory):
    user = factory.Faker("uuid4")
    time = factory.Faker("unix_milliseconds")


class TeamDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    created_at = factory.Faker("unix_milliseconds")


class ProjectDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    status = 'CREATED'
    created_at = factory.Faker("unix_milliseconds")
    team_id = factory.Faker('uuid4')


class DataVersionUpdateFactory(factory.DictFactory):
    current = "gemd::48e5e2f3-d447-458b-a8ea-d9cdb782b86e::1"
    latest = "gemd::48e5e2f3-d447-458b-a8ea-d9cdb782b86e::2"


class PredictorRefFactory(factory.DictFactory):
    predictor_id = factory.Faker('uuid4')
    predictor_version = factory.Faker('random_digit_not_null')


class BranchDataUpdateFactory(factory.DictFactory):
    data_updates = factory.List([factory.SubFactory(DataVersionUpdateFactory)])
    predictors = factory.List([factory.SubFactory(PredictorRefFactory)])


class NextBranchVersionFactory(factory.DictFactory):
    data_updates = factory.List([factory.SubFactory(DataVersionUpdateFactory)])
    predictors = factory.List([factory.SubFactory(PredictorRefFactory)])


class BranchDataFieldFactory(factory.DictFactory):
    name = factory.Faker('company')


class BranchMetadataFieldFactory(factory.DictFactory):
    root_id = factory.Faker('uuid4')
    archived = factory.Faker('boolean')
    version = factory.Faker('random_digit_not_null')
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)


class BranchDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(BranchDataFieldFactory)
    metadata = factory.SubFactory(BranchMetadataFieldFactory)


class BranchVersionRefFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    version = factory.Faker('random_digit_not_null')


class BranchRootMetadataFieldFactory(factory.DictFactory):
    latest_branch_version = factory.SubFactory(BranchVersionRefFactory)
    archived = factory.Faker('boolean')
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)


class BranchRootDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(BranchDataFieldFactory)
    metadata = factory.SubFactory(BranchRootMetadataFieldFactory)


class UserDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    screen_name = factory.Faker('name')
    position = factory.Faker('job')
    email = factory.Faker('email')
    is_admin = factory.Faker('boolean')


class GemTableDataFactory(factory.DictFactory):
    """Individual GemTable responses.

    Returned from the URL:
    * gem-tables/{table_identity_id}/versions/{table_version_id}
    * table-configs/{table_config_uid_str}/gem-tables
    """

    id = factory.Faker('uuid4')
    version = factory.Faker('random_digit_not_null')
    signed_download_url = factory.Faker('uri')


class ListGemTableVersionsDataFactory(factory.DictFactory):
    """List-based GemTable responses.

    Returned from the URLs:
    * gem-tables/
    * gem-tables/{table_identity_id}
    """
    # Explicitly set version numbers so that they are distinct
    tables = factory.List([
        factory.SubFactory(GemTableDataFactory, version=1),
        factory.SubFactory(GemTableDataFactory, version=4),
        factory.SubFactory(GemTableDataFactory, version=2),
    ])


class RealFilterDataFactory(factory.DictFactory):
    type = AllRealFilter.typ
    unit = 'dimensionless'
    lower = factory.LazyAttribute(lambda o: min(0, 2 * o.upper) + random() * o.upper)
    upper = factory.Faker("pyfloat")


class IntegerFilterDataFactory(factory.DictFactory):
    type = AllIntegerFilter.typ
    lower = factory.LazyAttribute(lambda o: randint(min(0, 2 * o.upper), o.upper))
    upper = factory.Faker("pyint")


class CategoryFilterDataFactory(factory.DictFactory):
    type = NominalCategoricalFilter.typ
    categories = factory.Faker('words', unique=True)


class PropertiesCriteriaDataFactory(factory.DictFactory):
    type = PropertiesCriteria.typ
    property_templates_filter = factory.List([factory.Faker('uuid4')])
    value_type_filter = factory.SubFactory(RealFilterDataFactory)

    class Params:
        integer = factory.Trait(
            value_type_filter=factory.SubFactory(IntegerFilterDataFactory)
        )
        category = factory.Trait(
            value_type_filter=factory.SubFactory(CategoryFilterDataFactory)
        )


class NameCriteriaDataFactory(factory.DictFactory):
    type = NameCriteria.typ
    name = factory.Faker('word')
    search_type = factory.Faker('enum', enum_cls=TextSearchType)


class MaterialRunClassificationCriteriaDataFactory(factory.DictFactory):
    type = MaterialRunClassificationCriteria.typ
    classifications = factory.Faker(
        'random_elements',
        elements=[str(x) for x in MaterialClassification],
        unique=True
    )


class MaterialTemplatesCriteriaDataFactory(factory.DictFactory):
    type = MaterialTemplatesCriteria.typ
    material_templates_identifiers = factory.List([factory.Faker('uuid4')])
    tag_filters = factory.Faker('words', unique=True)


class AndOperatorCriteriaDataFactory(factory.DictFactory):
    type = AndOperator.typ
    criteria = factory.List([
        factory.SubFactory(NameCriteriaDataFactory),
        factory.SubFactory(MaterialRunClassificationCriteriaDataFactory),
        factory.SubFactory(MaterialTemplatesCriteriaDataFactory)
    ])


class OrOperatorCriteriaDataFactory(factory.DictFactory):
    type = OrOperator.typ
    criteria = factory.List([
        factory.SubFactory(PropertiesCriteriaDataFactory),
        factory.SubFactory(PropertiesCriteriaDataFactory, integer=True),
        factory.SubFactory(PropertiesCriteriaDataFactory, category=True),
        factory.SubFactory(AndOperatorCriteriaDataFactory)
    ])


class GemdQueryDataFactory(factory.DictFactory):
    criteria = factory.List([factory.SubFactory(OrOperatorCriteriaDataFactory)])
    datasets = factory.List([factory.Faker('uuid4')])
    object_types = factory.List([str(x) for x in GemdObjectType])
    schema_version = 1


class TableConfigMainMetaDataDataFactory(factory.DictFactory):
    """This is the metadata for the primary definition ID of the TableConfig."""
    id = factory.Faker('uuid4')
    deleted = False
    create_time = factory.Faker("unix_milliseconds")
    created_by = factory.Faker('uuid4')
    update_time = factory.Faker("unix_milliseconds")
    updated_by = factory.Faker('uuid4')


class TableConfigDataFactory(factory.DictFactory):
    """This is simply the Blob stored in a Table Config Version."""
    name = factory.Faker("company")
    description = factory.Faker('bs')
    # TODO  Create factories for definitions
    rows = []
    columns = []
    variables = []
    datasets = factory.List([factory.Faker('uuid4')])
    gemd_query = factory.SubFactory(GemdQueryDataFactory)


class TableConfigVersionMetaDataDataFactory(factory.DictFactory):
    ara_definition = factory.SubFactory(TableConfigDataFactory)
    id = factory.Faker('uuid4')
    definition_id = factory.Faker('uuid4')
    version_number = factory.Faker('random_digit_not_null')
    deleted = False
    create_time = factory.Faker("unix_milliseconds")
    created_by = factory.Faker('uuid4')
    update_time = factory.Faker("unix_milliseconds")
    updated_by = factory.Faker('uuid4')
    initiator = str(TableConfigInitiator.CITRINE_PYTHON)


class TableConfigResponseDataFactory(factory.DictFactory):
    """This is the TableConfig object that encapsulates both version and definition info from the server.

    It is returned from the URLs:
    * projects/{project_id}/display-tables/{uid}/versions/{version}/definition

    """
    definition = factory.SubFactory(TableConfigMainMetaDataDataFactory)
    version = factory.SubFactory(TableConfigVersionMetaDataDataFactory)


class ListTableConfigResponseDataFactory(factory.DictFactory):
    """This encapsulates all of the versions of a table config object."""
    definition = factory.SubFactory(TableConfigMainMetaDataDataFactory)
    # Explicitly set version numbers so that they are distinct
    versions = factory.List([
        factory.SubFactory(TableConfigVersionMetaDataDataFactory, version_number=1),
        factory.SubFactory(TableConfigVersionMetaDataDataFactory, version_number=4),
        factory.SubFactory(TableConfigVersionMetaDataDataFactory, version_number=2),
    ])


class TableDataSourceDataFactory(factory.DictFactory):
    type = "hosted_table_data_source"
    table_id = factory.Faker("uuid4")
    table_version = factory.Faker('random_digit_not_null')

from citrine.informatics.data_sources import GemTableDataSource

class TableDataSourceFactory(factory.Factory):
    class Meta:
        model = GemTableDataSource

    class Params:
        data_factory = factory.SubFactory(TableDataSourceDataFactory)

    table_id = factory.LazyAttribute(lambda o: o.data_factory["table_id"])
    table_version = factory.LazyAttribute(lambda o: o.data_factory["table_version"])


class StatusDataFactory(factory.DictFactory):
    # TODO  Create trait and info / detail content
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
    predictors = []  # TODO  Create PredictorDataFactory
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


class AsyncDefaultPredictorResponseMetadataFactory(factory.DictFactory):
    data_source = factory.SubFactory(TableDataSourceDataFactory)
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)
    # TODO  Create Trait and status_detail content
    status = "INPROGRESS"
    status_detail = []


class AsyncDefaultPredictorResponseDataFactory(factory.DictFactory):
    name = factory.LazyAttribute(lambda data: data.instance["name"])
    description = factory.LazyAttribute(lambda data: data.instance["description"])
    instance = factory.SubFactory(PredictorInstanceDataFactory)
    output = []  # TODO  Create output content


class AsyncDefaultPredictorResponseFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    metadata = factory.SubFactory(AsyncDefaultPredictorResponseMetadataFactory)
    data = factory.SubFactory(AsyncDefaultPredictorResponseDataFactory)


class PredictorEvaluationWorkflowDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker("company")
    description = factory.Faker("catch_phrase")
    archived = False
    evaluators = []  # TODO  Create EvaluatorDataFactory
    type = "PredictorEvaluationWorkflow"
    # TODO  Create Trait and status_detail content
    status = "SUCCEEDED"
    status_description = "READY"
    status_detail = []


class DesignSpaceConfigDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker("company")
    descriptor = factory.Faker("catch_phrase")
    subspaces = []  # TODO  Create SubspaceDataFactory
    dimensions = []  # TODO  Create DimensionDataFactory
    type = "ProductDesignSpace"


class DesignSpaceDataFactory(factory.DictFactory):
    config = factory.SubFactory(DesignSpaceConfigDataFactory)
    id = factory.Faker('uuid4')
    display_name = factory.Faker("company")
    archived = False
    module_type = "DESIGN_SPACE"
    # TODO  Create Trait and status_detail content
    status = "READY"
    status_detail = []


class DesignWorkflowDataFactory(factory.DictFactory):
    class Params:
        data_source = factory.SubFactory(TableDataSourceFactory)
        branch = factory.SubFactory(BranchDataFactory)
        times = factory.List([factory.Faker("unix_milliseconds") for i in range(3)])
        register = factory.Trait(
            id = factory.Faker('uuid4'),
            branch_id = factory.LazyAttribute(lambda o: o.branch["id"]),
            created_by = factory.Faker('uuid4'),
            updated_by = factory.LazyAttribute(lambda o: o.created_by),
            create_time = factory.LazyAttribute(lambda o: sorted(o.times)[0]),
            update_time = factory.LazyAttribute(lambda o: sorted(o.times)[0]),
            # TODO: Create a Trait for statuses
            status = "SUCCEEDED",
            status_description = "READY",
            status_info = [],
            status_detail = []
        )
        update = factory.Trait(
            register = True,
            updated_by = factory.Faker('uuid4'),
            update_time = factory.LazyAttribute(lambda o: sorted(o.times)[1])
        )
        archive = factory.Trait(
            update = True,
            archived = True,
            archived_by = factory.Faker('uuid4'),
            archive_time = factory.LazyAttribute(lambda o: sorted(o.times)[2]),
        )

    type = DesignWorkflow.typ
    name = factory.Faker("company")
    description = factory.Faker("catch_phrase")
    design_space_id = factory.Faker("uuid4")
    predictor_id = factory.Faker("uuid4")
    predictor_version = factory.Faker("random_digit_not_null")
    data_source_id = factory.LazyAttribute(lambda o: o.data_source.to_data_source_id())
    branch_root_id = factory.LazyAttribute(lambda o: o.branch["metadata"]["root_id"])
    branch_version = factory.LazyAttribute(lambda o: o.branch["metadata"]["version"])
    archived = False
    status_description = ""  # TODO: Should be None, but property not defined as Optional


class IngestFilesResponseDataFactory(factory.DictFactory):
    team_id = factory.Faker('uuid4')
    dataset_id = factory.Faker('uuid4')
    ingestion_id = factory.Faker('uuid4')


class IngestionStatusResponseDataFactory(factory.DictFactory):
    ingestion_id = factory.Faker('uuid4')
    status = IngestionStatusType.INGESTION_CREATED
    errors = factory.List([])


class JobSubmissionResponseDataFactory(factory.DictFactory):
    job_id = factory.Faker('uuid4')


class TaskNodeDataFactory(factory.DictFactory):
    class Params:
        failure = False

    id = factory.Faker('uuid4')
    task_type = factory.Faker('word')
    status = factory.Maybe(
        "failure",
        yes_declaration=JobStatus.FAILURE,
        no_declaration=JobStatus.SUCCESS
    )
    dependencies = factory.List([])
    failure_reason = factory.Maybe(
        "failure",
        yes_declaration=factory.Faker('sentence'),
        no_declaration=None
    )


class JobStatusResponseDataFactory(factory.DictFactory):
    class Params:
        failure = False

    job_type = factory.Faker('word')
    status = factory.Maybe(
        "failure",
        yes_declaration=JobStatus.FAILURE,
        no_declaration=JobStatus.SUCCESS
    )
    tasks = factory.List([
        factory.RelatedFactory(TaskNodeDataFactory, failure=factory.SelfAttribute('...failure'))
    ])
    output = factory.Dict({})


class DatasetDataFactory(factory.DictFactory):
    class Params:
        times = factory.List([factory.Faker("unix_milliseconds") for i in range(3)])

    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')
    deleted = False
    created_by = factory.Faker('uuid4')
    updated_by = factory.Faker('uuid4')
    deleted_by = factory.Faker('uuid4')
    unique_name = None  # TODO Update tests to include unique_name
    create_time = factory.LazyAttribute(lambda o: sorted(o.times)[0])
    update_time = factory.LazyAttribute(lambda o: sorted(o.times)[1])
    delete_time = factory.LazyAttribute(lambda o: sorted(o.times)[2])
    public = False


class IDDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')


class LinkByUIDFactory(factory.Factory):
    class Meta:
        model = LinkByUID

    scope = 'id'
    id = factory.Faker('uuid4')


class FileLinkFactory(factory.Factory):
    class Meta:
        model = FileLink

    url = factory.Faker('uri')
    filename = factory.Faker('file_name')


class ProcessTemplateFactory(factory.Factory):
    class Meta:
        model = ProcessTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = factory.List([factory.Faker('color_name'), factory.Faker('color_name')])
    description = factory.Faker('catch_phrase')
    conditions = []  # TODO make a ConditionsTemplateFactory
    parameters = []  # TODO make a ParametersTemplateFactory


class MaterialTemplateFactory(factory.Factory):
    class Meta:
        model = MaterialTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = factory.List([factory.Faker('color_name'), factory.Faker('color_name')])
    properties = []  # TODO make a PropertiesTemplateFactory
    description = factory.Faker('catch_phrase')


class MaterialSpecFactory(factory.Factory):
    class Meta:
        model = MaterialSpec

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = factory.List([factory.Faker('color_name'), factory.Faker('color_name')])
    notes = factory.Faker('catch_phrase')
    process = factory.SubFactory(LinkByUIDFactory)
    file_links = factory.List([factory.SubFactory(FileLinkFactory)])
    template = factory.SubFactory(LinkByUIDFactory)
    properties = []  # TODO make a PropertiesFactory


class MaterialRunFactory(factory.Factory):
    class Meta:
        model = MaterialRun

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = factory.List([factory.Faker('color_name'), factory.Faker('color_name')])
    notes = factory.Faker('catch_phrase')
    process = factory.SubFactory(LinkByUIDFactory)
    sample_type = factory.Faker("enum", enum_cls=SampleType)
    spec = factory.SubFactory(LinkByUIDFactory)
    file_links = factory.List([factory.SubFactory(FileLinkFactory)])


class LinkByUIDDataFactory(factory.DictFactory):
    id = LinkByUIDFactory.id
    scope = LinkByUIDFactory.scope
    type = 'link_by_uid'


class FileLinkDataFactory(factory.DictFactory):
    url = FileLinkFactory.url
    filename = FileLinkFactory.filename
    type = 'file_link'


class MaterialSpecDataFactory(factory.DictFactory):
    uids = MaterialSpecFactory.uids
    name = MaterialSpecFactory.name
    tags = MaterialSpecFactory.tags
    notes = MaterialSpecFactory.notes
    process = factory.SubFactory(LinkByUIDDataFactory)
    file_links = factory.List([factory.SubFactory(FileLinkDataFactory)])
    template = factory.SubFactory(LinkByUIDDataFactory)
    properties = []  # TODO make a PropertiesDataFactory
    type = 'material_spec'


class MaterialRunDataFactory(factory.DictFactory):
    uids = MaterialRunFactory.uids
    name = MaterialRunFactory.name
    tags = MaterialRunFactory.tags
    notes = MaterialRunFactory.notes
    process = factory.SubFactory(LinkByUIDDataFactory)
    sample_type = MaterialRunFactory.sample_type
    spec = factory.SubFactory(LinkByUIDDataFactory)
    file_links = factory.List([factory.SubFactory(FileLinkDataFactory)])
    type = 'material_run'


class DatasetFactory(factory.Factory):
    class Meta:
        model = Dataset

    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')
    unique_name = None  # TODO Update tests to include unique_name


class _UploaderFactory(factory.Factory):
    class Meta:
        model = _Uploader

    # TODO Bring _Uploader in line with other library concepts
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

    baselines = []  # TODO make a BaselineDataFactory
    objectives = []  # TODO make an ObjectiveDataFactory
    constraints = []  # TODO make a ConstraintDataFactory


class CategoricalExperimentValueDataFactory(factory.DictFactory):
    type = "CategoricalValue"
    value = factory.Faker('company')


class ChemicalFormulaExperimentValueDataFactory(factory.DictFactory):
    type = "InorganicValue"
    value = factory.Faker('random_formula')


class IntegerExperimentValueDataFactory(factory.DictFactory):
    type = "IntegerValue"
    value = factory.Faker('random_int', min=1, max=99)


class MixtureExperimentValueDataFactory(factory.DictFactory):
    type = "MixtureValue"
    value = factory.Dict({"ingredient1": 0.3, "ingredient2": 0.7})


class MolecularStructureExperimentValueDataFactory(factory.DictFactory):
    type = "OrganicValue"
    value = factory.Faker('random_smiles')


class RealExperimentValueDataFactory(factory.DictFactory):
    type = "RealValue"
    value = factory.Faker('pyfloat', min_value=0, max_value=100)


class CandidateExperimentSnapshotDataFactory(factory.DictFactory):
    experiment_id = factory.Faker('uuid4')
    candidate_id = factory.Faker('uuid4')
    workflow_id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('company')
    updated_time = factory.Faker("unix_milliseconds")
    # TODO  Generate Experiment keys randomly but uniquely
    overrides = factory.Dict({
        "ingredient1": factory.SubFactory(CategoricalExperimentValueDataFactory),
        "ingredient2": factory.SubFactory(ChemicalFormulaExperimentValueDataFactory),
        "ingredient3": factory.SubFactory(IntegerExperimentValueDataFactory),
        "Formulation": factory.SubFactory(MixtureExperimentValueDataFactory),
        "ingredient4": factory.SubFactory(MolecularStructureExperimentValueDataFactory),
        "ingredient5": factory.SubFactory(RealExperimentValueDataFactory)
    })


class ExperimentDataSourceDataDataFactory(factory.DictFactory):
    experiments = factory.List([factory.SubFactory(CandidateExperimentSnapshotDataFactory)])


class ExperimentDataSourceMetadataDataFactory(factory.DictFactory):
    branch_root_id = factory.Faker('uuid4')
    version = factory.Faker('random_digit_not_null')
    created = factory.SubFactory(UserTimestampDataFactory)


class ExperimentDataSourceDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(ExperimentDataSourceDataDataFactory)
    metadata = factory.SubFactory(ExperimentDataSourceMetadataDataFactory)


class AnalysisPlotMetadataDataFactory(factory.DictFactory):
    rank = factory.Faker('random_int', min=1, max=10)
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)


class AnalysisPlotDataDataFactory(factory.DictFactory):
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    plot_type = factory.Faker('random_element', elements=('SCATTER', 'VIOLIN'))
    config = {}


class AnalysisPlotEntityDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(AnalysisPlotDataDataFactory)
    metadata = factory.SubFactory(AnalysisPlotMetadataDataFactory)


class LatestBuildDataFactory(factory.DictFactory):
    class Params:
        is_failed = factory.LazyAttribute(lambda o: o.status == 'FAILED')

    status = factory.Faker('random_element', elements=('INPROGRESS', 'SUCCEEDED', 'FAILED'))
    failure_reason = factory.Maybe('is_failed', ['This is a test failure message'], [])
    query = factory.SubFactory(GemdQueryDataFactory)


class AnalysisWorkflowMetadataDataFactory(factory.DictFactory):
    class Meta:
        exclude = ('is_archived', 'has_build')

    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)
    archived = factory.Maybe('is_archived', factory.SubFactory(UserTimestampDataFactory), None)
    latest_build = factory.Maybe('has_build', factory.SubFactory(LatestBuildDataFactory), None)


class AnalysisWorkflowDataDataFactory(factory.DictFactory):
    class Meta:
        exclude = ('has_snapshot', 'plot_count')

    class Params:
        plot_count = 1

    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    snapshot_id = factory.Maybe('has_snapshot', factory.Faker('uuid4'), None)
    plots = factory.LazyAttribute(lambda self: [AnalysisPlotEntityDataFactory() for _ in range(self.plot_count)])


class AnalysisWorkflowEntityDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    data = factory.SubFactory(AnalysisWorkflowDataDataFactory)
    metadata = factory.SubFactory(AnalysisWorkflowMetadataDataFactory)


class FeatureEffectsResponseResultFactory(factory.DictFactory):
    materials = factory.List([
        factory.Faker('uuid4', cast_to=None),
        factory.Faker('uuid4', cast_to=None),
        factory.Faker('uuid4', cast_to=None)
    ])
    outputs = factory.Dict({
        "output1": factory.Dict({
            "feature1": factory.List([factory.Faker("pyfloat"), factory.Faker("pyfloat"), factory.Faker("pyfloat")])
        }),
        "output2": factory.Dict({
            "feature1": factory.List([factory.Faker("pyfloat"), factory.Faker("pyfloat"), factory.Faker("pyfloat")]),
            "feature2": factory.List([factory.Faker("pyfloat"), factory.Faker("pyfloat"), factory.Faker("pyfloat")])
        })
    })

class FeatureEffectsMetadataFactory(factory.DictFactory):
    predictor_id = factory.Faker('uuid4')
    predictor_version = factory.Faker('random_digit_not_null')
    created = factory.SubFactory(UserTimestampDataFactory)
    updated = factory.SubFactory(UserTimestampDataFactory)
    status = 'SUCCEEDED'


class FeatureEffectsResponseFactory(factory.DictFactory):
    query = {}  # Presently, querying from the SDK is not allowed.
    metadata = factory.SubFactory(FeatureEffectsMetadataFactory)
    result = factory.SubFactory(FeatureEffectsResponseResultFactory)
    _result_as_dict = factory.LazyAttribute(lambda obj: _expand_condensed(obj.result))


def _expand_condensed(result_obj):
    if not result_obj:
        return None

    whole_dict = {}
    for output, feature_dict in result_obj["outputs"].items():
        whole_dict[output] = {}
        for feature, values in feature_dict.items():
            whole_dict[output][feature] = dict(zip(result_obj["materials"], values))
    return whole_dict
