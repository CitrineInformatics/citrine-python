from uuid import uuid4
import pytest
import mock

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
from citrine.resources.table_config import TableConfig, TableConfigCollection, TableBuildAlgorithm
from citrine._rest.collection import Collection

from citrine.builders.auto_configure import AutoConfigureWorkflow, AutoConfigureMode, AutoConfigureStatus


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


# Define a fake collection/module interface for testing our fake project
class FakeCollection(Collection):
    def __init__(self):
        pass

    def register(self, asset):
        asset.uid = uuid4()
        return asset


class FakeTableConfigCollection(FakeCollection, TableConfigCollection):
    def __init__(self):
        pass

    def default_for_material(self, **kwargs):
        return FakeTableConfig(), []


class FakeGemTableCollection(FakeCollection, GemTableCollection):
    def __init__(self):
        pass

    def build_from_config(self, *args, **kwargs) -> GemTable:
        table = FakeGemTable()
        table.version = 1
        table.uid = uuid4()  # Returns a registered object for real
        return table


class FakePredictorCollection(FakeCollection, PredictorCollection):
    def __init__(self):
        pass

    def auto_configure(self, **kwargs) -> Predictor:
        predictor = FakePredictor()
        return predictor


class FakePredictorEvaluationWorkflowCollection(FakeCollection, PredictorEvaluationWorkflowCollection):
    def __init__(self):
        pass

    def create_default(self, **kwargs) -> PredictorEvaluationWorkflow:
        return FakePredictorEvaluationWorkflow()


class FakePredictorEvaluationExecutionCollection(FakeCollection, PredictorEvaluationExecutionCollection):
    def __init__(self):
        pass

    def trigger(self, *args):
        return FakePredictorEvaluationExecution()


class FakeDesignSpaceCollection(FakeCollection, DesignSpaceCollection):
    def __init__(self):
        pass

    def create_default(self, **kwargs) -> DesignSpace:
        return FakeDesignSpace()


class FakeDesignWorkflowCollection(FakeCollection, DesignWorkflowCollection):
    def __init__(self):
        pass


class FakeDesignExecutionCollection(FakeCollection, DesignExecutionCollection):
    def __init__(self):
        pass

    def trigger(self, *args):
        return FakeDesignExecution()


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


@pytest.fixture()
def fake_project():
    """Fake project that returns auto-configured assets."""

    class FakeProject(Project):

        def __init__(self):
            pass

        @property
        def table_configs(self) -> TableConfigCollection:
            return FakeTableConfigCollection()

        @property
        def tables(self) -> GemTableCollection:
            return FakeGemTableCollection()

        @property
        def predictors(self) -> PredictorCollection:
            return FakePredictorCollection()

        @property
        def predictor_evaluation_workflows(self) -> PredictorEvaluationWorkflowCollection:
            return FakePredictorEvaluationWorkflowCollection()

        @property
        def predictor_evaluation_executions(self) -> PredictorEvaluationExecutionCollection:
            return FakePredictorEvaluationExecutionCollection()

        @property
        def design_spaces(self) -> DesignSpaceCollection:
            return FakeDesignSpaceCollection()

        @property
        def design_workflows(self) -> DesignWorkflowCollection:
            return FakeDesignWorkflowCollection()

    return FakeProject()


@pytest.fixture()
def fake_config(fake_project: Project):
    return AutoConfigureWorkflow(project=fake_project, name='Fake v1')


def test_auto_configure_public_raises(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_mr = MaterialRun(name='Fake Material')
    fake_table = fake_project.tables.build_from_config()
    fake_predictor = fake_project.predictors.auto_configure()

    # Raises on bad mode
    with pytest.raises(TypeError):
        fake_config.from_material(
            material=fake_mr,
            mode='BAD MODE TYPE'
        )

    with pytest.raises(TypeError):
        fake_config.from_table(
            table=fake_table,
            mode='BAD MODE TYPE'
        )

    # Raises on no predictor UID
    with pytest.raises(ValueError):
        fake_config.from_predictor(
            predictor=fake_predictor
        )


@mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready)
@mock.patch('citrine.builders.auto_configure.PredictorEvaluationWorkflow', FakePredictorEvaluationWorkflow)
@mock.patch('citrine.builders.auto_configure.DesignWorkflow', FakeDesignWorkflow)
def test_auto_configure_public_interface(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_mr = MaterialRun(name='Fake Material')
    score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Test Key')], baselines=[0.0])

    # Basic properties
    assert(fake_config.name == 'Fake v1')
    assert(fake_config.status_info == [])

    # Cannot execute design until you run the auto-config
    with pytest.raises(ValueError):
        fake_config.execute(score=score)

    # Run through the entire workflow, creating all assets
    assert(fake_config.status == AutoConfigureStatus.START.value)
    fake_config.from_material(material=fake_mr, mode=AutoConfigureMode.PLAIN, score=score)
    assert(len(fake_config.assets) == 8)
    assert(fake_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_CREATED.value)
    assert(fake_config.status_info[0] == 'Something went very right.')


def test_auto_configure_table_build_stage(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_mr = MaterialRun(name='Fake Material')

    assert(fake_config.status == AutoConfigureStatus.START.value)
    fake_config._table_build_stage(material=fake_mr, mode=AutoConfigureMode.PLAIN)

    assert(fake_config.status == AutoConfigureStatus.TABLE_CREATED.value)
    assert(fake_config.table_config is not None)
    assert(fake_config.table is not None)
    assert(len(fake_config.assets) == 2)


def test_auto_configure_predictor_build_stage(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_table = fake_project.tables.build_from_config()

    # When predictor is valid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
        assert(len(fake_config.assets) == 0)
        fake_config._predictor_build_stage(
            table=fake_table,
            mode=AutoConfigureMode.PLAIN,
            print_status_info=False
        )
        assert(fake_config.predictor is not None)
        assert(len(fake_config.assets) == 1)
        assert(fake_config.status == AutoConfigureStatus.PREDICTOR_CREATED.value)

    # When predictor is invalid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_invalid):
        with pytest.raises(RuntimeError):
            fake_config._predictor_build_stage(
                table=fake_table,
                mode=AutoConfigureMode.PLAIN,
                print_status_info=False
            )
        assert(fake_config.status == AutoConfigureStatus.PREDICTOR_INVALID.value)


@mock.patch('citrine.builders.auto_configure.PredictorEvaluationWorkflow', FakePredictorEvaluationWorkflow)
def test_auto_configure_predictor_evaluation_stage(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_predictor = fake_project.predictors.auto_configure()
    evaluator = CrossValidationEvaluator(name='Test Evaluator', responses={'Test Key'})

    # When PEW is valid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
        fake_config._predictor_evaluation_stage(
            predictor=fake_predictor,
            evaluator=None,
            print_status_info=False
        )
        assert(len(fake_config.assets) == 2)
        assert(fake_config.predictor_evaluation_workflow is not None)
        assert(fake_config.predictor_evaluation_execution is not None)
        assert(fake_config.status == AutoConfigureStatus.PEW_CREATED.value)

        # Mock creation of real one inside
        fake_config._predictor_evaluation_stage(
            predictor=fake_predictor,
            evaluator=evaluator,
            print_status_info=False
        )
        assert(fake_config.predictor_evaluation_workflow.name == 'Fake v1 - Predictor Evaluation Workflow')

    # When PEW fails
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_failed):
        fake_config._predictor_evaluation_stage(
            predictor=fake_predictor,
            evaluator=None,
            print_status_info=False
        )
        assert(fake_config.status == AutoConfigureStatus.PEW_FAILED.value)


def test_auto_configure_design_space_build_stage(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_predictor = fake_project.predictors.auto_configure()
    design_space = EnumeratedDesignSpace(name='Test DS', description = '', descriptors=[], data=[])

    # When design space is valid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
        fake_config._design_space_build_stage(
            predictor=fake_predictor,
            design_space=None,
            print_status_info=False
        )
        assert(fake_config.design_space is not None)
        assert(len(fake_config.assets) == 1)
        assert(fake_config.status == AutoConfigureStatus.DESIGN_SPACE_CREATED.value)

        # Only accepts data source design space
        with pytest.raises(TypeError):
            fake_config._design_space_build_stage(
                predictor=fake_predictor,
                design_space=design_space,
                print_status_info=False
            )

    # When design space is invalid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_invalid):
        with pytest.raises(RuntimeError):
            fake_config._design_space_build_stage(
                predictor=fake_predictor,
                design_space=None,
                print_status_info=False
            )


@mock.patch('citrine.builders.auto_configure.DesignWorkflow', FakeDesignWorkflow)
def test_auto_configure_design_workflow_build_stage(fake_config: AutoConfigureWorkflow, fake_project: Project):
    fake_predictor = fake_project.predictors.auto_configure()
    fake_design_space = fake_project.design_spaces.create_default()
    score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Test Key')], baselines=[0.0])

    # When design space is valid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_ready):
        # First with no score provided
        fake_config._design_workflow_build_stage(
            predictor=fake_predictor, design_space=fake_design_space,
            score=None, print_status_info=False
        )
        assert(fake_config.design_workflow is not None)
        assert(fake_config.design_execution is None)
        assert(len(fake_config.assets) == 1)
        assert(fake_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_CREATED.value)

        # And now with a score
        fake_config._design_workflow_build_stage(
            predictor=fake_predictor, design_space=fake_design_space,
            score=score, print_status_info=False
        )
        assert(fake_config.design_execution is not None)
        assert(len(fake_config.assets) == 2)

    # When design space is invalid
    with mock.patch('citrine.builders.auto_configure.wait_while_validating', wait_while_failed):
        with pytest.raises(RuntimeError):
            fake_config._design_workflow_build_stage(
                predictor=fake_predictor, design_space=fake_design_space,
                score=score, print_status_info=False
            )
        # With no score, no error, despite DW failing
        # Check status to show it failed
        fake_config._design_workflow_build_stage(
            predictor=fake_predictor, design_space=fake_design_space,
            score=None, print_status_info=False
        )
        assert(fake_config.status == AutoConfigureStatus.DESIGN_WORKFLOW_FAILED.value)
