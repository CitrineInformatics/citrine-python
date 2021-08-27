from uuid import uuid4

import pytest
import mock

from citrine.builders.auto_configure import AutoConfigureWorkflow, AutoConfigureMode

from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.informatics.predictors import GraphPredictor
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
from citrine.informatics.objectives import ScalarMaxObjective
from citrine.informatics.scores import LIScore

from citrine._session import Session
from citrine.resources.gemtables import GemTable
from citrine.resources.material_run import MaterialRun
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig

from tests.utils.session import FakeSession
from tests.utils.fakes import FakeDesignWorkflow, FakePredictorEvaluationWorkflow
from tests.utils.fakes import FakeProject
from tests.utils.wait import generate_fake_wait_while

# Return functions that mock wait_while_validating with specified status
fake_wait_while_ready = generate_fake_wait_while(status="READY")
fake_wait_while_succeeded = generate_fake_wait_while(status="SUCCEEDED")
fake_wait_while_invalid = generate_fake_wait_while(status="INVALID")
fake_wait_while_failed = generate_fake_wait_while(status="FAILED")


@pytest.fixture
def session() -> Session:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    return FakeProject(name="Test Project", description="", session=session)


def default_resources(name):
    table_config = TableConfig(
        name=f"{name}: Auto Configure GEM Table",
        description="", rows=[], variables=[], columns=[], datasets=[]
    )
    predictor = GraphPredictor(
        name=f"{name}: Auto Configure Predictor", description="", predictors=[]
    )
    pew = FakePredictorEvaluationWorkflow(
        name=f"{name}: Auto Configure PEW", description="", evaluators=[]
    )
    design_space = EnumeratedDesignSpace(
        name=f"{name}: Auto Configure Design Space", description="", descriptors=[], data=[]
    )
    # Workflow must be fake to get appropriate execution collection
    workflow = FakeDesignWorkflow(
        name=f"{name}: Auto Configure Design Workflow",
        predictor_id=uuid4(),
        design_space_id=uuid4(),
        processor_id=uuid4()
    )
    return {
        "table_config": table_config,
        "predictor": predictor,
        "pew": pew,
        "design_space": design_space,
        "design_workflow": workflow
    }


def test_auto_config_mode_raises(project):
    """Test that we raise errors on bad mode choices."""
    config_name = "Test"
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)

    with pytest.raises(TypeError):
        auto_config.from_material(material=MaterialRun(name="Fake"), mode="BAD CHOICE")

    with pytest.raises(TypeError):
        auto_config.from_table(table=GemTable(), mode="BAD CHOICE")


def test_auto_configure_properties(project):
    """Test the property access on the auto config workflow."""
    config_name = "Test"
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)

    assert auto_config.design_execution is None
    assert auto_config.score is None
    assert len(auto_config.candidates) == 0


def test_auto_config_init(project):
    """Test that the update calls during initialization find appropriate assets."""
    config_name = "Test"
    resources = default_resources(config_name)

    # No assets added to project yet, nothing to find
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 0
    assert auto_config.status == "START"
    assert auto_config.status_info == []

    # Add a table/table_config
    project.table_configs.register(resources["table_config"])
    project.tables.build_from_config(resources["table_config"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 2
    assert auto_config.status == "TABLE CREATED"

    # Add a predictor
    project.predictors.register(resources["predictor"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 3
    assert auto_config.status == "PREDICTOR CREATED"

    # Add a PEW
    project.predictor_evaluation_workflows.register(resources["pew"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 4
    assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"

    # Add a design space
    project.design_spaces.register(resources["design_space"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 5
    assert auto_config.status == "DESIGN SPACE CREATED"

    # Add a design workflow
    project.design_workflows.register(resources["design_workflow"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW CREATED"


def test_auto_config_update_status(project):
    """Test that update finds the appropriate status."""
    config_name = "Test"
    resources = default_resources(config_name)
    table_config = resources["table_config"]
    predictor= resources["predictor"]
    pew = resources["pew"]
    design_space = resources["design_space"]
    design_workflow = resources["design_workflow"]

    # Create an auto config, blank status
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 0
    assert auto_config.status == "START"

    # Give it a table, check status
    project.table_configs.register(table_config)
    project.tables.build_from_config(table_config)
    auto_config.update()
    assert len(auto_config.assets) == 2
    assert auto_config.status == "TABLE CREATED"

    # Give it predictor, check status
    project.predictors.register(predictor)
    auto_config.update()
    assert len(auto_config.assets) == 3
    assert auto_config.status == "PREDICTOR CREATED"

    predictor.status = "INVALID"
    project.predictors.update(predictor)
    auto_config.update()
    assert len(auto_config.assets) == 3
    assert auto_config.status == "PREDICTOR INVALID"

    # Give it PEWS, check status
    project.predictor_evaluation_workflows.register(pew)
    auto_config.update()
    assert len(auto_config.assets) == 4
    assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"

    pew.status = "FAILED"
    project.predictor_evaluation_workflows.update(pew)
    auto_config.update()
    assert len(auto_config.assets) == 4
    assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"

    # Give it design spaces, check status
    project.design_spaces.register(design_space)
    auto_config.update()
    assert len(auto_config.assets) == 5
    assert auto_config.status == "DESIGN SPACE CREATED"

    design_space.status = "INVALID"
    project.design_spaces.update(design_space)
    auto_config.update()
    assert len(auto_config.assets) == 5
    assert auto_config.status == "DESIGN SPACE INVALID"

    # Give it design workflows, check status
    project.design_workflows.register(design_workflow)
    auto_config.update()
    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW CREATED"

    design_workflow.status = "FAILED"
    project.design_workflows.update(design_workflow)
    auto_config.update()
    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW FAILED"


def test_auto_config_execute(project):
    """Test the score execution on auto config workflow."""
    config_name = "Test"
    resources = default_resources(config_name)
    project.table_configs.register(resources["table_config"])
    project.predictors.register(resources["predictor"])
    project.predictor_evaluation_workflows.register(resources["pew"])
    project.design_spaces.register(resources["design_space"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert auto_config.design_workflow is None

    # Inputs for execute
    objective = ScalarMaxObjective(descriptor_key="Fake Target")

    with pytest.raises(ValueError):
        auto_config.execute(score=objective)

    # Now create a config with a working design workflow
    project.design_workflows.register(resources["design_workflow"])
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert auto_config.status == "DESIGN WORKFLOW CREATED"

    # Mock function to bypass create_default_score call internally
    def _default_score(*args, **kwargs):
        return LIScore(objectives=[], baselines=[])

    with mock.patch("citrine.builders.auto_configure.create_default_score", _default_score):
        auto_config.execute(score=objective)
        assert auto_config.design_execution is not None


def test_auto_config_table_build(project):
    """Test the table build stage of auto configure."""
    config_name = "Test"
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 0

    auto_config._table_build_stage(
        material="Fake Material",
        mode=AutoConfigureMode.PLAIN
    )
    assert len(auto_config.assets) == 2


def test_auto_configure_predictor_registration(project):
    """Test the predictor registration stage of auto configure."""
    # Start from having a table config and table
    config_name = "Test"
    resources = default_resources(config_name)
    project.table_configs.register(resources["table_config"])
    project.tables.build_from_config(resources["table_config"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 2
    assert auto_config.status == "TABLE CREATED"

    # Inputs to pass to method
    predictor = resources["predictor"]

    # Mock a valid predictor response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_ready):
        auto_config._predictor_registration_stage(
            predictor=predictor,
            print_status_info=False
        )
        assert len(auto_config.assets) == 3
        assert auto_config.status == "PREDICTOR CREATED"

    # Mock an invalid predictor response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_invalid):
        with pytest.raises(RuntimeError):
            auto_config._predictor_registration_stage(
                predictor=predictor,
                print_status_info=False
            )
        assert len(auto_config.assets) == 3
        assert auto_config.status == "PREDICTOR INVALID"


@mock.patch("citrine.builders.auto_configure.PredictorEvaluationWorkflow", FakePredictorEvaluationWorkflow)
def test_auto_configure_predictor_evaluation(project):
    """Test the predictor evaluation stage of auto configure."""
    config_name = "Test"
    resources = default_resources(config_name)
    project.table_configs.register(resources["table_config"])
    project.tables.build_from_config(resources["table_config"])
    project.predictors.register(resources["predictor"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 3
    assert auto_config.status == "PREDICTOR CREATED"

    # Inputs to pass to method
    predictor = resources["predictor"]
    evaluator = CrossValidationEvaluator(name="Eval", description="", responses=set())

    # Create default w/ a valid response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_succeeded):
        auto_config._predictor_evaluation_stage(
            predictor=predictor,
            evaluator=None,
            print_status_info=False
        )
        assert len(auto_config.assets) == 4
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"

    # Create default w/ an invalid response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_failed):
        auto_config._predictor_evaluation_stage(
            predictor=predictor,
            evaluator=None,
            print_status_info=False
        )
        assert len(auto_config.assets) == 4
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"

    # Create manual w/ a valid response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_succeeded):
        auto_config._predictor_evaluation_stage(
            predictor=predictor,
            evaluator=evaluator,
            print_status_info=False
        )
        assert len(auto_config.assets) == 4
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"

    # Create manual w/ a failed response
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_failed):
        auto_config._predictor_evaluation_stage(
            predictor=predictor,
            evaluator=evaluator,
            print_status_info=False
        )
        assert len(auto_config.assets) == 4
        assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"


def test_auto_configure_design_space_build(project):
    """Test the design space build stage of auto configure."""
    config_name = "Test"
    resources = default_resources(config_name)
    project.table_configs.register(resources["table_config"])
    project.tables.build_from_config(resources["table_config"])
    project.predictors.register(resources["predictor"])
    project.predictor_evaluation_workflows.register(resources["pew"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 4
    assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"

    # Inputs to pass to method
    predictor = resources["predictor"]
    design_space = resources["design_space"]

    # When validation succeeds
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_ready):
        auto_config._design_space_build_stage(
            predictor=predictor,
            design_space=design_space,
            print_status_info=False
        )
        assert len(auto_config.assets) == 5
        assert auto_config.status == "DESIGN SPACE CREATED"

    # When validation fails
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_invalid):
        with pytest.raises(RuntimeError):
            auto_config._design_space_build_stage(
                predictor=predictor,
                design_space=design_space,
                print_status_info=False
            )
        assert auto_config.status == "DESIGN SPACE INVALID"


@mock.patch.object(AutoConfigureWorkflow, "execute", lambda *args, **kwargs: None)
def test_auto_configure_design_workflow_build(project):
    """Test the design workflow build stage of auto configure."""
    config_name = "Test"
    resources = default_resources(config_name)
    project.table_configs.register(resources["table_config"])
    project.tables.build_from_config(resources["table_config"])
    project.predictors.register(resources["predictor"])
    project.predictor_evaluation_workflows.register(resources["pew"])
    project.design_spaces.register(resources["design_space"])

    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 5
    assert auto_config.status == "DESIGN SPACE CREATED"

    # Inputs to pass to method
    predictor = resources["predictor"]
    design_space = resources["design_space"]
    score = LIScore(objectives=[], baselines=[])

    # When validation succeeds
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_succeeded):
        auto_config._design_workflow_build_stage(
            predictor=predictor,
            design_space=design_space,
            score=score,
            print_status_info=False
        )
        assert len(auto_config.assets) == 6
        assert auto_config.status == "DESIGN WORKFLOW CREATED"

    # When validation fails
    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_failed):
        with pytest.raises(RuntimeError):
            auto_config._design_workflow_build_stage(
                predictor=predictor,
                design_space=design_space,
                score=score,
                print_status_info=False
            )
        assert len(auto_config.assets) == 6
        assert auto_config.status == "DESIGN WORKFLOW FAILED"

        # With no score passed, should not raise error
        auto_config._design_workflow_build_stage(
            predictor=predictor,
            design_space=design_space,
            score=None,
            print_status_info=False
        )
        assert auto_config.status == "DESIGN WORKFLOW FAILED"


def test_auto_configure_full_run(project):
    """Test the full chain of public methods, from_material -> from_table -> from_predictor."""
    config_name = "Test"
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)
    assert len(auto_config.assets) == 0
    assert auto_config.status == "START"

    # Create input material
    material = MaterialRun(name="I am fake.")

    with mock.patch("citrine.builders.auto_configure.wait_while_validating", fake_wait_while_ready):
        auto_config.from_material(
            material=material,
            mode=AutoConfigureMode.PLAIN,
            print_status_info=False
        )
        assert len(auto_config.assets) == 6
        assert auto_config.status == "DESIGN WORKFLOW CREATED"

