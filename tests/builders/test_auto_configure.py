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


# Resources
class FakeTableConfig(TableConfig):
    def __init__(self, name: str):
        self.name = name


class FakeGemTable(GemTable):
    def __init__(self):
        pass


class FakePredictor(Predictor):
    def __init__(self, name: str, *, status: str = "VALID"):
        self.name = name
        self.status = status
        self.status_info = []


class FakePredictorEvaluationWorkflow(PredictorEvaluationWorkflow):
    def __init__(self, name: str, *, status: str = "SUCCEEDED"):
        self.name = name
        self.status = status
        self.status_info = []

    @property
    def executions(self):
        return FakePredictorEvaluationExecutionCollection()


class FakePredictorEvaluationExecution(PredictorEvaluationExecution):
    def __init__(self):
        pass


class FakeDesignSpace(DesignSpace):
    def __init__(self, name: str, *, status: str = "VALID"):
        self.name = name
        self.status = status
        self.status_info = []


class FakeDesignWorkflow(DesignWorkflow):
    def __init__(self, name: str, *, status: str = "SUCCEEDED"):
        self.name = name
        self.status = status
        self.status_info = []

    @property
    def design_executions(self):
        return FakeDesignExecutionCollection()


class FakeDesignExecution(DesignExecution):
    def __init__(self):
        pass

    def candidates(self):
        return []


# Define a fake collection/module interface for testing our fake project
class FakeTableConfigCollection:
    def __init__(self):
        pass

    def default_for_material(self, **kwargs):
        return FakeTableConfig(), []

    def get(self, uid):
        config = FakeTableConfig("Test: Auto Configure GEM Table")
        config.uid = uuid4()
        config.version = 1
        return config


class FakeGemTableCollection:
    def __init__(self):
        pass

    def build_from_config(self, config):
        table = FakeGemTable()
        table.version = 1
        table.uid = uuid4()  # Returns a registered object for real
        return table

    def list_by_config(self, config):
        yield self.build_from_config(config)


class FakePredictorCollection:
    def __init__(self):
        pass

    def auto_configure(self, *, training_data, pattern):
        predictor = FakePredictor()
        predictor.uid = uuid4()
        return predictor


class FakePredictorEvaluationWorkflowCollection:
    def __init__(self):
        pass

    def create_default(self, *, predictor_id):
        return FakePredictorEvaluationWorkflow()


class FakePredictorEvaluationExecutionCollection:
    def __init__(self):
        pass

    def trigger(self, *args):
        return FakePredictorEvaluationExecution()

    def list(self):
        yield FakePredictorEvaluationExecution()


class FakeDesignSpaceCollection:
    def __init__(self):
        pass

    def create_default(self, **kwargs) -> DesignSpace:
        return FakeDesignSpace()


class FakeDesignWorkflowCollection:
    def __init__(self):
        pass


class FakeDesignExecutionCollection:
    def __init__(self):
        pass

    def trigger(self, *args):
        return FakeDesignExecution()

    def list(self):
        yield FakeDesignExecution()


@pytest.fixture()
def project():
    """Fake project that binds to fake collections."""
    class FakeProject(Project):
        def __init__(self):
            pass

        @property
        def table_configs(self):
            return FakeTableConfigCollection()

        @property
        def tables(self):
            return FakeGemTableCollection()

        @property
        def predictors(self):
            return FakePredictorCollection()

        @property
        def predictor_evaluation_workflows(self):
            return FakePredictorEvaluationWorkflowCollection()

        @property
        def design_spaces(self):
            return FakeDesignSpaceCollection()

        @property
        def design_workflows(self):
            return FakeDesignWorkflowCollection()

    return FakeProject()


@pytest.fixture
def resources():
    """A resource holder to pull find_collection results from."""
    class ResourceHolder:
        def __init__(self):
            self.resources = []

        def register(self, model):
            self.resources.append(model)

        def find(self, name: str):
            for model in self.resources:
                if model.name == name:
                    return model
            return None

        def pop(self):
            return self.resources.pop()

        def clear(self):
            self.resources.clear()

    return ResourceHolder()


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


def test_auto_configure_update_stages(project, resources):
    """Test updating assets and state works as intended."""

    def mock_find_collection(*, collection, name):
        return resources.find(name)

    with mock.patch("citrine.builders.auto_configure.find_collection", mock_find_collection):
        # Finds nothing, blank slate
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 0
        assert auto_config.status == "START"

        # Finds only a table and table config
        resources.register(FakeTableConfig("Test: Auto Configure GEM Table"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 2
        assert auto_config.status == "TABLE CREATED"
        resources.clear()

        # Finds up to predictor with VALID status
        resources.register(FakePredictor("Test: Auto Configure Predictor"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "PREDICTOR CREATED"
        resources.clear()

        # Finds up to predictor with INVALID status
        resources.register(FakePredictor("Test: Auto Configure Predictor", status="INVALID"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "PREDICTOR INVALID"
        resources.clear()

        # Finds a PEW with SUCCEEDED status
        resources.register(FakePredictorEvaluationWorkflow("Test: Auto Configure PEW"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"
        resources.clear()

        # Finds a PEW with FAILED status
        resources.register(FakePredictorEvaluationWorkflow("Test: Auto Configure PEW", status="FAILED"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"
        resources.clear()

        # Finds a design space with VALID status
        resources.register(FakeDesignSpace("Test: Auto Configure Design Space", status="VALID"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "DESIGN SPACE CREATED"
        resources.clear()

        # Finds a design space with INVALID status
        resources.register(FakeDesignSpace("Test: Auto Configure Design Space", status="INVALID"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "DESIGN SPACE INVALID"
        resources.clear()

        # Finds a design workflow with SUCCEEDED status
        resources.register(FakeDesignWorkflow("Test: Auto Configure Design Workflow"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "DESIGN WORKFLOW CREATED"
        resources.clear()

        # Finds a design workflow with FAILED status
        resources.register(FakeDesignWorkflow("Test: Auto Configure Design Workflow", status="FAILED"))
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 1
        assert auto_config.status == "DESIGN WORKFLOW FAILED"
        resources.clear()

def test_auto_configure_update_get(project, resources):
    """Test updating assets and state works as intended."""

    def mock_find_collection(*, collection, name):
        return resources.find(name)

    # Create a full workflow with all assets found
    all_resources = [
        FakeTableConfig("Test: Auto Configure GEM Table"),
        FakePredictor("Test: Auto Configure Predictor"),
        FakePredictorEvaluationWorkflow("Test: Auto Configure PEW"),
        FakeDesignSpace("Test: Auto Configure Design Space"),
        FakeDesignWorkflow("Test: Auto Configure Design Workflow")
    ]
    for model in all_resources:
        resources.register(model)

    with mock.patch("citrine.builders.auto_configure.find_collection", mock_find_collection):
        auto_config = AutoConfigureWorkflow(project=project, name="Test")
        assert len(auto_config.assets) == 6
        assert auto_config.status == "DESIGN WORKFLOW CREATED"

        auto_config.update()
        assert len(auto_config.assets) == 6



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
