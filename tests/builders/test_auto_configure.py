from uuid import uuid4, UUID
import pytest
import mock

from tests.utils.factories import *
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


# @pytest.fixture()
# def project():
#     """Fake project that binds to fake collections."""
#     class FakeProject(Project):
#         def __init__(self):
#             pass
#
#         @property
#         def table_configs(self):
#             return FakeTableConfigCollection()
#
#         @property
#         def tables(self):
#             return FakeGemTableCollection()
#
#         @property
#         def predictors(self):
#             return FakePredictorCollection()
#
#         @property
#         def predictor_evaluation_workflows(self):
#             return FakePredictorEvaluationWorkflowCollection()
#
#         @property
#         def design_spaces(self):
#             return FakeDesignSpaceCollection()
#
#         @property
#         def design_workflows(self):
#             return FakeDesignWorkflowCollection()
#
#     return FakeProject()


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


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    return Project("Test", session=session)


@pytest.fixture
def table_config_data():
    data = TableConfigResponseDataFactory()
    data["version"]["ara_definition"]["name"] = "Test: Auto Configure GEM Table"
    return data


@pytest.fixture
def table_data():
    data = GemTableDataFactory()
    return data


@pytest.fixture
def predictor_data():
    data = PredictorDataFactory()
    data["config"]["name"] = "Test: Auto Configure Predictor"
    return data


@pytest.fixture
def pew_data():
    data = PredictorEvaluationWorkflowDataFactory()
    data["name"] = "Test: Auto Configure PEW"
    return data

@pytest.fixture
def design_space_data():
    data = DesignSpaceDataFactory()
    data["config"]["name"] = "Test: Auto Configure Design Space"
    return data

@pytest.fixture
def design_workflow_data():
    data = DesignWorkflowDataFactory()
    data["name"] = "Test: Auto Configure Design Workflow"
    return data


@pytest.fixture
def data_holder(
    table_config_data,
    table_data,
    predictor_data,
    pew_data,
    design_space_data,
    design_workflow_data
):
    class DataHolder:
        table_config = table_config_data
        table = table_data
        predictor = predictor_data
        pew = pew_data
        design_space = design_space_data
        design_workflow = design_workflow_data
    return DataHolder


def test_list(project, session, data_holder):
    session.set_responses(
        {"definitions": [data_holder.table_config]},
        {"tables": [data_holder.table]},
        {"entries": [data_holder.predictor]},
        {"response": [data_holder.pew]},
        {"entries": [data_holder.design_space]},
        {"response": [data_holder.design_workflow]}
    )

    # Test initial update, find all
    auto_config = AutoConfigureWorkflow(project=project, name="Test")
    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW CREATED"

    # Reset data for update run
    session.set_responses(
        {"versions": [data_holder.table_config]},
    )

    auto_config.update()





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