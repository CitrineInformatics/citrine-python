from uuid import uuid4, UUID
import pytest
import mock

from tests.utils.session import FakeSession

from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import LIScore

from citrine.resources.design_execution import DesignExecution, DesignExecutionCollection
from citrine.resources.design_space import DesignSpace, DesignSpaceCollection
from citrine.resources.design_workflow import DesignWorkflow, DesignWorkflowCollection
from citrine.resources.gemtables import GemTable, GemTableCollection
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import Predictor, GraphPredictor, PredictorCollection
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflow
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflowCollection
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig, TableConfigCollection
from citrine._rest.collection import Collection

from citrine.builders.auto_configure import AutoConfigureWorkflow, AutoConfigureMode, AutoConfigureStatus


# Define a fake collection/module interface for testing our fake project
class FakeCollection(Collection):
    def __init__(self):
        pass

    def register(self, asset):
        # Fake no-op for testing
        return asset


class FakeTableConfigCollection(FakeCollection, TableConfigCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def default_for_material(self, **kwargs):
        return FakeTableConfig(), []


    def get(self, uid):
        config = FakeTableConfig()


class FakeGemTableCollection(FakeCollection, GemTableCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def build_from_config(self, *args, **kwargs) -> GemTable:
        table = FakeGemTable()
        table.version = 1
        table.uid = uuid4()  # Returns a registered object for real
        return table

    def list_by_config(self, table_config_uid):
        yield self.build_from_config()


class FakePredictorCollection(FakeCollection, PredictorCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def auto_configure(self, **kwargs) -> Predictor:
        predictor = FakePredictor()
        predictor.uid = uuid4()
        return predictor


class FakePredictorEvaluationWorkflowCollection(FakeCollection, PredictorEvaluationWorkflowCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def create_default(self, **kwargs) -> PredictorEvaluationWorkflow:
        return FakePredictorEvaluationWorkflow()


class FakePredictorEvaluationExecutionCollection(FakeCollection, PredictorEvaluationExecutionCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def trigger(self, *args):
        return FakePredictorEvaluationExecution()

    def list(self):
        yield FakePredictorEvaluationExecution()


class FakeDesignSpaceCollection(FakeCollection, DesignSpaceCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def create_default(self, **kwargs) -> DesignSpace:
        return FakeDesignSpace()


class FakeDesignWorkflowCollection(FakeCollection, DesignWorkflowCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

class FakeDesignExecutionCollection(FakeCollection, DesignExecutionCollection):
    def __init__(self, project_id, session):
        self.project_id = project_id
        self.session = session

    def trigger(self, *args):
        return FakeDesignExecution()

    def list(self):
        yield FakeDesignExecution()

# Resources
class FakeTableConfig(TableConfig):
    def __init__(self):
        pass


class FakeGemTable(GemTable):
    def __init__(self):
        pass


class FakePredictor(Predictor):
    def __init__(self):
        pass


class FakePredictorEvaluationWorkflow(PredictorEvaluationWorkflow):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', '')

    @property
    def executions(self) -> PredictorEvaluationExecutionCollection:
        return FakePredictorEvaluationExecutionCollection()


class FakePredictorEvaluationExecution(PredictorEvaluationExecution):
    def __init__(self):
        pass


class FakeDesignSpace(DesignSpace):
    def __init__(self):
        pass


class FakeDesignWorkflow(DesignWorkflow):
    def __init__(self, **kwargs):
        pass

    @property
    def design_executions(self) -> DesignExecutionCollection:
        return FakeDesignExecutionCollection()


class FakeDesignExecution(DesignExecution):
    def __init__(self):
        pass

    def candidates(self):
        return []


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture()
def project(session):
    """Fake project that returns auto-configured assets."""

    class FakeProject(Project):
        def __init__(self, *, session):
            self.session = session
            self.uid = UUID('6b608f78-e341-422c-8076-35adc8828545')

        @property
        def table_configs(self) -> TableConfigCollection:
            return FakeTableConfigCollection(self.uid, self.session)

        @property
        def tables(self) -> GemTableCollection:
            return FakeGemTableCollection(self.uid, self.session)

        @property
        def predictors(self) -> PredictorCollection:
            return FakePredictorCollection(self.uid, self.session)

        @property
        def predictor_evaluation_workflows(self) -> PredictorEvaluationWorkflowCollection:
            return FakePredictorEvaluationWorkflowCollection(self.uid, self.session)

        @property
        def design_spaces(self) -> DesignSpaceCollection:
            return FakeDesignSpaceCollection(self.uid, self.session)

        @property
        def design_workflows(self) -> DesignWorkflowCollection:
            return FakeDesignWorkflowCollection(self.uid, self.session)

    return FakeProject(session=session)


@pytest.fixture()
def auto_config(project):
    with mock.patch('citrine.builders.auto_configure.find_collection', fake_find_collection):
        config = AutoConfigureWorkflow(project=project, name='Test')
        yield config


def wait_while_ready(*, module, **kwargs):
    """Mock mutations of a successful module validation."""
    module.status = 'READY'
    module.status_info = ['Something went very right.']
    return module


def wait_while_invalid(*, module, **kwargs):
    """Mock mutations of a failed module validation."""
    module.status = 'INVALID'
    module.status_info = ['Something went very wrong.']
    return module


def wait_while_failed(*, module, **kwargs):
    """Mock mutations of a failed workflow validation."""
    module.status = 'FAILED'
    module.status_info = ['Something went very wrong.']
    return module


def fake_find_collection(*, collection, name):
    """Return predefined resources given the naming conventions."""
    assets = {
        "Test: Auto Configure GEM Table": FakeGemTable(),
        "Test: Auto Configure Predictor": FakePredictor(),
        "Test: Auto Configure PEW": FakePredictorEvaluationWorkflow(),
        "Test: Auto Configure Design Space": FakeDesignSpace(),
        "Test: Auto Configure Design Workflow": FakeDesignWorkflow(),
    }
    return assets[name]


def fake_create_or_update(*, collection, resource):
    return fake_find_collection(collection=collection, name=resource.name)


def test_auto_configure_update(auto_config, session):
    # Initialization searches via fake_find_collection
    assert auto_config.name == "Test"
    assert len(auto_config.assets) == 6

    # Set response for get calls during update
    session.set_responses([None, None, None, None, None, None])

    auto_config.update()


# def test_auto_configure_mode_raises(auto_config, fake_project):
#     fake_mr = MaterialRun(name='Fake Material')
#     fake_table = fake_project.tables.build_from_config()
#
#     # Raises on bad mode
#     with pytest.raises(TypeError):
#         auto_config.from_material(
#             material=fake_mr,
#             mode='BAD MODE TYPE'
#         )
#
#     with pytest.raises(TypeError):
#         auto_config.from_table(
#             table=fake_table,
#             mode='BAD MODE TYPE'
#         )


# @mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready)
# @mock.patch('citrine.builders.auto_configure.PredictorEvaluationWorkflow', FakePredictorEvaluationWorkflow)
# @mock.patch('citrine.builders.auto_configure.DesignWorkflow', FakeDesignWorkflow)
# def test_auto_configure_public_interface(auto_config: AutoConfigureWorkflow):
#     fake_mr = MaterialRun(name='Fake Material')
#     score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Test Key')], baselines=[0.0])
#
#     # Basic properties
#     assert(auto_config.name == 'Test')
#     assert(len(auto_config.assets) == 6)  # Found initial during find_collection
#
#     #
#     # # Run through the entire workflow, creating all assets
#     # assert(auto_config.status == AutoConfigureStatus.START.value)
#     # auto_config.from_material(material=fake_mr, mode=AutoConfigureMode.PLAIN, score=score)
#     # assert(len(auto_config.assets) == 8)
#     # assert(auto_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_CREATED.value)
#     # assert(auto_config.status_info[0] == 'Something went very right.')
#
#
# def test_auto_configure_table_build_stage(auto_config):
#     fake_mr = MaterialRun(name='Fake Material')
#
#     assert(auto_config.status == AutoConfigureStatus.START.value)
#     auto_config._table_build_stage(material=fake_mr, mode=AutoConfigureMode.PLAIN)
#
#     assert(auto_config.status == AutoConfigureStatus.TABLE_CREATED.value)
#     assert(auto_config.table_config is not None)
#     assert(auto_config.table is not None)
#     assert(len(auto_config.assets) == 2)
#
#
# def test_auto_configure_predictor_registration_stage(auto_config, fake_project):
#     fake_table = fake_project.tables.build_from_config()
#
#     # When predictor is valid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
#         assert(len(auto_config.assets) == 0)
#         auto_config._predictor_build_stage(
#             table=fake_table,
#             mode=AutoConfigureMode.PLAIN,
#             print_status_info=False
#         )
#         assert(auto_config.predictor is not None)
#         assert(len(auto_config.assets) == 1)
#         assert(auto_config.status == AutoConfigureStatus.PREDICTOR_CREATED.value)
#
#     # When predictor is invalid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_invalid):
#         with pytest.raises(RuntimeError):
#             auto_config._predictor_build_stage(
#                 table=fake_table,
#                 mode=AutoConfigureMode.PLAIN,
#                 print_status_info=False
#             )
#         assert(auto_config.status == AutoConfigureStatus.PREDICTOR_INVALID.value)
#
#
# @mock.patch('citrine.builders.auto_configure.PredictorEvaluationWorkflow', FakePredictorEvaluationWorkflow)
# def test_auto_configure_predictor_evaluation_stage(auto_config, fake_project):
#     fake_predictor = fake_project.predictors.auto_configure()
#     evaluator = CrossValidationEvaluator(name='Test Evaluator', responses={'Test Key'})
#
#     # When PEW is valid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
#         auto_config._predictor_evaluation_stage(
#             predictor=fake_predictor,
#             evaluator=None,
#             print_status_info=False
#         )
#         assert(len(auto_config.assets) == 2)
#         assert(auto_config.predictor_evaluation_workflow is not None)
#         assert(auto_config.predictor_evaluation_execution is not None)
#         assert(auto_config.status == AutoConfigureStatus.PEW_CREATED.value)
#
#         # Mock creation of real one inside
#         auto_config._predictor_evaluation_stage(
#             predictor=fake_predictor,
#             evaluator=evaluator,
#             print_status_info=False
#         )
#         assert(auto_config.predictor_evaluation_workflow.name == 'Fake v1 - Predictor Evaluation Workflow')
#
#     # When PEW fails
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_failed):
#         auto_config._predictor_evaluation_stage(
#             predictor=fake_predictor,
#             evaluator=None,
#             print_status_info=False
#         )
#         assert(auto_config.status == AutoConfigureStatus.PEW_FAILED.value)
#
#
# def test_auto_configure_design_space_build_stage(auto_config, fake_project):
#     fake_predictor = fake_project.predictors.auto_configure()
#     design_space = EnumeratedDesignSpace(name='Test DS', description = '', descriptors=[], data=[])
#
#     # When design space is valid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
#         auto_config._design_space_build_stage(
#             predictor=fake_predictor,
#             design_space=None,
#             print_status_info=False
#         )
#         assert(auto_config.design_space is not None)
#         assert(len(auto_config.assets) == 1)
#         assert(auto_config.status == AutoConfigureStatus.DESIGN_SPACE_CREATED.value)
#
#         # Test when providing a design space
#         auto_config._design_space_build_stage(
#             predictor=fake_predictor,
#             design_space=design_space,
#             print_status_info=False
#         )
#
#     # When design space is invalid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_invalid):
#         with pytest.raises(RuntimeError):
#             auto_config._design_space_build_stage(
#                 predictor=fake_predictor,
#                 design_space=None,
#                 print_status_info=False
#             )
#
#
# @mock.patch('citrine.builders.auto_configure.DesignWorkflow', FakeDesignWorkflow)
# def test_auto_configure_design_workflow_build_stage(auto_config, fake_project):
#     fake_predictor = fake_project.predictors.auto_configure()
#     fake_design_space = fake_project.design_spaces.create_default()
#     score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Test Key')], baselines=[0.0])
#
#     # When design space is valid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
#         # First with no score provided
#         auto_config._design_workflow_build_stage(
#             predictor=fake_predictor, design_space=fake_design_space,
#             score=None, print_status_info=False
#         )
#         assert(auto_config.design_workflow is not None)
#         assert(auto_config.design_execution is None)
#         assert(len(auto_config.assets) == 1)
#         assert(auto_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_CREATED.value)
#
#         # And now with a score
#         auto_config._design_workflow_build_stage(
#             predictor=fake_predictor, design_space=fake_design_space,
#             score=score, print_status_info=False
#         )
#         assert(auto_config.design_execution is not None)
#         assert(len(auto_config.assets) == 2)
#
#     # When design space is invalid
#     with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_failed):
#         with pytest.raises(RuntimeError):
#             auto_config._design_workflow_build_stage(
#                 predictor=fake_predictor, design_space=fake_design_space,
#                 score=score, print_status_info=False
#             )
#         # With no score, no error, despite DW failing
#         # Check status to show it failed
#         auto_config._design_workflow_build_stage(
#             predictor=fake_predictor, design_space=fake_design_space,
#             score=None, print_status_info=False
#         )
#         assert(auto_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_FAILED.value)
