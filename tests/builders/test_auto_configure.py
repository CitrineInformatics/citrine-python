from uuid import uuid4
import pytest
import mock

from citrine.builders.auto_configure import AutoConfigureWorkflow, AutoConfigureMode

from citrine.informatics.design_spaces import EnumeratedDesignSpace
from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
from citrine.informatics.objectives import ScalarMaxObjective

from citrine.resources.design_execution import DesignExecution
from citrine.resources.gemtables import GemTable
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import GraphPredictor
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.project import Project

from tests.utils.session import FakeSession
from tests.utils.fakes import FakeProject


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def project(session):
    return FakeProject(name="Test Project", session=session)


def test_auto_config_mode_raises(project):
    """Test that we raise errors on bad mode choices."""
    config_name = "Test"
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)

    with pytest.raises(TypeError):
        auto_config.from_material(
            material=MaterialRun(name="Fake"),
            mode="BAD CHOICE"
        )

    with pytest.raises(TypeError):
        auto_config.from_table(
            table=GemTable(),
            mode="BAD CHOICE"
        )


def test_auto_configure_properties(project, response_holder):
    """Test the property access on the auto config workflow."""
    config_name = "Test"
    response_holder.name = config_name
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)

    assert auto_config.design_execution is None
    assert auto_config.score is None
    assert len(auto_config.candidates) == 0


def test_auto_config_init(project, session, response_holder):
    """Test that the update calls during initialization find appropriate assets."""
    # Test initial update, find all by find_collection
    config_name = "Test"
    response_holder.name = config_name
    auto_config = AutoConfigureWorkflow(project=project, name=config_name)

    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW CREATED"

    # Reset data for update run, find all by get calls
    session.set_responses(
        response_holder.table_config_list,
        {"tables": [response_holder.table]},
        response_holder.predictor,
        response_holder.pew,
        response_holder.design_space,
        response_holder.design_workflow
    )
    auto_config.update()
    assert len(auto_config.assets) == 6
    assert auto_config.status == "DESIGN WORKFLOW CREATED"
    assert auto_config.status_info == []  # Not specified in fake data source


# @mock.patch("citrine.builders.auto_configure.create_default_score", fake_default_score)
# @mock.patch("citrine.resources.design_execution.DesignExecutionCollection.trigger", fake_de_trigger)
# def test_auto_config_execute(project, session, response_holder):
#     """Test the score execution on auto config workflow."""
#     config_name = "Test"
#     response_holder.name = config_name
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert auto_config.design_workflow is None
#
#     # Inputs for execute
#     objective = ScalarMaxObjective(descriptor_key="Fake Target")
#
#     with pytest.raises(ValueError):
#         auto_config.execute(score=objective)
#
#     # Now create a config with a working design workflow
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": [response_holder.design_workflow]}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert auto_config.status == "DESIGN WORKFLOW CREATED"
#
#     auto_config.execute(score=objective)
#     assert auto_config.design_execution is not None
#
#
# def test_auto_config_status(project, session, response_holder):
#     """Test that the status matches the found assets."""
#     # Find up to table config/table
#     config_name = "Test"
#     response_holder.name = config_name
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": []},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 2
#     assert auto_config.status == "TABLE CREATED"
#
#     # Find up to valid predictor
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 3
#     assert auto_config.status == "PREDICTOR CREATED"
#
#     # Find up to invalid predictor
#     response_holder.predictor["status"] = "INVALID"
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 3
#     assert auto_config.status == "PREDICTOR INVALID"
#
#     # Find up to successful PEW
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": []},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 4
#     assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"
#
#     # Find up to failed PEW
#     response_holder.pew["status"] = "FAILED"
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": []},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 4
#     assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"
#
#     # Find up to design space
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 5
#     assert auto_config.status == "DESIGN SPACE CREATED"
#
#     # Find up to invalid design space
#     response_holder.design_space["status"] = "INVALID"
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": []}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 5
#     assert auto_config.status == "DESIGN SPACE INVALID"
#
#     # Find up to design workflow
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": [response_holder.design_workflow]}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 6
#     assert auto_config.status == "DESIGN WORKFLOW CREATED"
#
#     # Find up to failed design workflow
#     response_holder.design_workflow["status"] = "FAILED"
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": [response_holder.design_workflow]}
#     )
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 6
#     assert auto_config.status == "DESIGN WORKFLOW FAILED"
#
#
# @mock.patch("citrine.resources.table_config.TableConfigCollection.default_for_material", fake_default_config)
# @mock.patch("citrine.resources.gemtables.GemTableCollection.build_from_config", fake_build_from_config)
# def test_auto_config_table_build(project, session, response_holder):
#     """Test the table build stage of auto configure."""
#     config_name = "Test"
#     response_holder.name = config_name
#     session.set_responses(
#         {"definitions": []},
#         {"entries": []},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 0
#
#     # Call the table build stage with mocked default calls
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         response_holder.table_config_response,
#     )
#     auto_config._table_build_stage(
#         material="Fake Material",
#         mode=AutoConfigureMode.PLAIN
#     )
#     assert len(auto_config.assets) == 2
#
#
# def test_auto_configure_predictor_registration(project, session, response_holder):
#     """Test the predictor registration stage of auto configure."""
#     # Start from having a table config and table
#     config_name = "Test"
#     response_holder.name = config_name
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": []},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 2
#     assert auto_config.status == "TABLE CREATED"
#
#     # Inputs to pass to method
#     predictor = GraphPredictor(name="Input", description="", predictors=[])
#
#     # Mock a valid predictor response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         session.set_responses(
#             {"entries": [response_holder.predictor]},
#         )
#         auto_config._predictor_registration_stage(
#             predictor=predictor,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 3
#         assert auto_config.status == "PREDICTOR CREATED"
#
#     # Mock an invalid predictor response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_invalid):
#         session.set_responses(
#             {"entries": [response_holder.predictor]},
#         )
#         with pytest.raises(RuntimeError):
#             auto_config._predictor_registration_stage(
#                 predictor=predictor,
#                 print_status_info=False
#             )
#         assert len(auto_config.assets) == 3
#         assert auto_config.status == "PREDICTOR INVALID"
#
#
# @mock.patch("citrine.resources.predictor_evaluation_execution.PredictorEvaluationExecutionCollection.trigger", fake_pee_trigger)
# @mock.patch("citrine.resources.predictor_evaluation_workflow.PredictorEvaluationWorkflowCollection.create_default", fake_default_pew)
# def test_auto_configure_predictor_evaluation(project, session, response_holder):
#     """Test the predictor evaluation stage of auto configure."""
#     config_name = "Test"
#     response_holder.name = config_name
#
#     # Start from up to predictor
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 3
#     assert auto_config.status == "PREDICTOR CREATED"
#
#     # Inputs to pass to method
#     predictor = GraphPredictor(name="Input", description="", predictors=[])
#     evaluator = CrossValidationEvaluator(name="Eval", description="", responses=set())
#
#     # Create default w/ a valid response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         auto_config._predictor_evaluation_stage(
#             predictor=predictor,
#             evaluator=None,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 4
#         assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"
#
#     # Create default w/ an invalid response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_failed):
#         auto_config._predictor_evaluation_stage(
#             predictor=predictor,
#             evaluator=None,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 4
#         assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"
#
#     # Create manual w/ a valid response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         session.set_responses(
#             {"response": [response_holder.pew]},
#             response_holder.pew
#         )
#         auto_config._predictor_evaluation_stage(
#             predictor=predictor,
#             evaluator=evaluator,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 4
#         assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"
#
#     # Create manual w/ a failed response
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_failed):
#         session.set_responses(
#             {"response": [response_holder.pew]},
#             response_holder.pew
#         )
#         auto_config._predictor_evaluation_stage(
#             predictor=predictor,
#             evaluator=evaluator,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 4
#         assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW FAILED"
#
# @mock.patch("citrine.resources.design_space.DesignSpaceCollection.create_default", fake_default_design_space)
# def test_auto_configure_design_space_build(project, session, response_holder):
#     """Test the design space build stage of auto configure."""
#     config_name = "Test"
#     response_holder.name = config_name
#
#     # Start from up to PEW
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 4
#     assert auto_config.status == "PREDICTOR EVALUATION WORKFLOW CREATED"
#
#     # Inputs to pass to method
#     predictor = GraphPredictor(name="Input", description="", predictors=[])
#     design_space = EnumeratedDesignSpace(name="DS", description="", descriptors=[], data=[])
#
#     # When validation succeeds
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         session.set_responses(
#             {"entries": [response_holder.design_space]}
#         )
#         auto_config._design_space_build_stage(
#             predictor=predictor,
#             design_space=design_space,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 5
#         assert auto_config.status == "DESIGN SPACE CREATED"
#
#     # When validation fails
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_invalid):
#         session.set_responses(
#             {"entries": [response_holder.design_space]}
#         )
#         with pytest.raises(RuntimeError):
#             auto_config._design_space_build_stage(
#                 predictor=predictor,
#                 design_space=design_space,
#                 print_status_info=False
#             )
#         assert auto_config.status == "DESIGN SPACE INVALID"
#
#
# @mock.patch("citrine.builders.auto_configure.AutoConfigureWorkflow.execute", fake_execute_score)
# def test_auto_configure_design_workflow_build(project, session, response_holder):
#     """Test the design workflow build stage of auto configure."""
#     config_name = "Test"
#     response_holder.name = config_name
#
#     # Start from up to design space
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},
#         {"tables": [response_holder.table]},
#         {"entries": [response_holder.predictor]},
#         {"response": [response_holder.pew]},
#         {"entries": [response_holder.design_space]},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 5
#     assert auto_config.status == "DESIGN SPACE CREATED"
#
#     # Inputs to pass to method
#     predictor = GraphPredictor(name="Input", description="", predictors=[])
#     design_space = EnumeratedDesignSpace(name="DS", description="", descriptors=[], data=[])
#     score = LIScore(objectives=[], baselines=[])
#     predictor.uid = uuid4()
#     design_space.uid = uuid4()
#
#     # When validation succeeds
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         session.set_responses(
#             {"response": [response_holder.design_workflow]},
#             response_holder.design_workflow
#         )
#         auto_config._design_workflow_build_stage(
#             predictor=predictor,
#             design_space=design_space,
#             score=score,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 6
#         assert auto_config.status == "DESIGN WORKFLOW CREATED"
#
#     # When validation fails
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_failed):
#         session.set_responses(
#             {"response": [response_holder.design_workflow]},
#             response_holder.design_workflow
#         )
#         with pytest.raises(RuntimeError):
#             auto_config._design_workflow_build_stage(
#                 predictor=predictor,
#                 design_space=design_space,
#                 score=score,
#                 print_status_info=False
#             )
#         assert len(auto_config.assets) == 6
#         assert auto_config.status == "DESIGN WORKFLOW FAILED"
#
#         # With no score passed, should not raise error
#         session.set_responses(
#             {"response": [response_holder.design_workflow]},
#             response_holder.design_workflow
#         )
#         auto_config._design_workflow_build_stage(
#             predictor=predictor,
#             design_space=design_space,
#             score=None,
#             print_status_info=False
#         )
#         assert auto_config.status == "DESIGN WORKFLOW FAILED"
#
#
# @mock.patch("citrine.resources.table_config.TableConfigCollection.default_for_material", fake_default_config)
# @mock.patch("citrine.resources.predictor.PredictorCollection.auto_configure", fake_predictor_auto_configure)
# @mock.patch("citrine.resources.gemtables.GemTableCollection.build_from_config", fake_build_from_config)
# @mock.patch("citrine.resources.predictor_evaluation_workflow.PredictorEvaluationWorkflowCollection.create_default", fake_default_pew)
# @mock.patch("citrine.resources.design_space.DesignSpaceCollection.create_default", fake_default_design_space)
# def test_auto_configure_full_run(project, session, response_holder):
#     """Test the full chain of public methods, from_material -> from_table -> from_predictor."""
#     config_name = "Test"
#     response_holder.name = config_name
#
#     # Start from empty
#     session.set_responses(
#         {"definitions": []},
#         {"entries": []},
#         {"response": []},
#         {"entries": []},
#         {"response": []}
#     )
#
#     auto_config = AutoConfigureWorkflow(project=project, name=config_name)
#     assert len(auto_config.assets) == 0
#     assert auto_config.status == "START"
#
#     # Create input material
#     material = MaterialRun(name="I am fake.")
#
#     # Set up the many responses needs to make it all the way through
#     # Each time create_or_update is called, we require two responses
#     #   One response for the find_collection call
#     #   and a second response for the update call
#     session.set_responses(
#         {"definitions": [response_holder.table_config_response]},  # Table build
#         response_holder.table_config_response,                     # Table build
#         {"entries": [response_holder.predictor]},                  # Predictor registration
#         response_holder.predictor,                                 # Predictor registration
#         {"entries": [response_holder.design_space]},               # Design space build
#         response_holder.design_space,                              # Design space build
#         {"response": [response_holder.design_workflow]},           # Design workflow build
#         response_holder.design_workflow                            # Design workflow build
#     )
#
#     with mock.patch("citrine.builders.auto_configure.wait_while_validating", wait_while_ready):
#         auto_config.from_material(
#             material=material,
#             mode=AutoConfigureMode.PLAIN,
#             print_status_info=False
#         )
#         assert len(auto_config.assets) == 6
#         assert auto_config.status == "DESIGN WORKFLOW CREATED"

