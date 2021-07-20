from uuid import UUID
from typing import Union, Optional, List
import warnings
import time

from gemd.entity.link_by_uid import LinkByUID
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.executions import DesignExecution, PredictorEvaluationExecution
from citrine.informatics.design_spaces import DesignSpace
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow, PredictorEvaluationWorkflow

from citrine.resources.gemtables import GemTable
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import Predictor
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig, TableBuildAlgorithm


class AutoConfigureMode(BaseEnumeration):
    """[ALPHA] The format to use in building auto-configured assets.

    * PLAIN corresponds to a single-row GEM table and plain predictor
    * FORMULATION corresponds to a multi-row GEM table and formulations predictor
    """

    PLAIN = 'PLAIN'
    FORMULATION = 'FORMULATION'


class AutoConfigureStatus(BaseEnumeration):
    """[ALPHA] The current status of the AutoConfigureWorkflow.

    * START is the initial status before auto-configuration
    * TABLE_BUILD is the status after creating a default GEM table
    * PREDICTOR_CREATED is the status after creating a default predictor
    * PREDICTOR_INVALID is the status if predictor validation fails
    * PEW_CREATED is the status after creating a predictor evaluation workflow
    * PEW_FAILED is the status if predictor evaluation workflow validation fails
    * DESIGN_SPACE_CREATED is the status after design space creation/registration
    * DESIGN_SPACE_INVALID is the status if design space validation fails
    * DESIGN_WORKFLOW_CREATED is the status after design workflow creation
    * DESIGN_WORKFlOW_FAILED is the status if design workflow validation fails
    """

    START = 'START'
    TABLE_CREATED = 'TABLE CREATED'
    PREDICTOR_CREATED = 'PREDICTOR CREATED'
    PREDICTOR_INVALID = 'PREDICTOR INVALID'
    PEW_CREATED = 'PREDICTOR EVALUATION WORKFLOW CREATED'
    PEW_FAILED = 'PREDICTOR EVALUATION WORKFLOW FAILED'
    DESIGN_SPACE_CREATED = 'DESIGN SPACE CREATED'
    DESIGN_SPACE_INVALID = 'DESIGN SPACE INVALID'
    DESIGN_WORKFLOW_CREATED = 'DESIGN WORKFLOW CREATED'
    DESIGN_WORKFLOW_FAILED = 'DESIGN WORKFLOW FAILED'


class AutoConfigureWorkflow():
    """[ALPHA] Helper class for configuring and storing default assets on the Citrine Platform.

    Defines methods for creating a default GEM table, predictor, predictor evaluations,
    design space, design workflow, and design execution in a linear fashion,
    starting from a provided material/table/predictor.

    All assets that are registered to the Citrine Platform
    during the auto configuration steps are stored as members of this class.
    In case this method fails during asset validation,
    the previously configured items are accessible
    locally and on the Citrine Platform for later use or modification.

    Example usage:
    ```
    # Initialize score and workflow
    score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Desc 1'), baselines=[1.0])
    auto_config = AutoConfigureWorkflow(project=project, name='Auto Config v1')

    # GEM table -> Predictor -> PEW/PEE -> Design Space -> Design Workflow -> Design Execution
    auto_config.from_material(
        material=sample_material,
        score=score,
        mode=AutoConfigureMode.PLAIN,
        print_status_info=True
    )

    # Check the most recent status
    print(f"Workflow ended with status: {auto_config.status}")

    # Retrieve some of the results
    table = auto_config.table
    predictor = auto_config.predictor
    execution = auto_config.design_execution
    ```

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform.
    name: str
        Name to affix to auto-configured assets on the Citrine Platform.
        Default: ''

    """

    def __init__(self, *, project: Project, name: str = ''):
        self._project = project
        self._name = name
        self._prefix = '{} - '.format(name) if name else ''
        self._status = AutoConfigureStatus.START
        self._status_info = []

        # Blank initialize assets
        self._table_config = None
        self._table = None
        self._predictor = None
        self._predictor_evaluation_workflow = None
        self._predictor_evaluation_execution = None
        self._design_space = None
        self._design_workflow = None
        self._design_execution = None

    @property
    def project(self) -> Project:
        """Get the project used when automatically configuring assets."""
        return self._project

    @property
    def name(self) -> str:
        """Get the naming label for assets configured by this object."""
        return self._name

    @property
    def status(self) -> str:
        """Get the most recent status of the auto-configure workflow."""
        return self._status.value

    @property
    def status_info(self) -> List[str]:
        """Get the most recent status info from asset configuration/validation."""
        return self._status_info

    @property
    def table_config(self) -> Optional[TableConfig]:
        """Get the default table config, if it was created by this object."""
        return self._table_config

    @property
    def table(self) -> Optional[GemTable]:
        """Get the default GEM table, if it was created by this object."""
        return self._table

    @property
    def predictor(self) -> Optional[Predictor]:
        """Get the default predictor, if it was created by this object."""
        return self._predictor

    @property
    def predictor_evaluation_workflow(self) -> Optional[PredictorEvaluationWorkflow]:
        """Get the predictor evaluation workflow, if it was created by this object."""
        return self._predictor_evaluation_workflow

    @property
    def predictor_evaluation_execution(self) -> Optional[PredictorEvaluationExecution]:
        """Get the predictor evaluation execution, if it was created by this object."""
        return self._predictor_evaluation_execution

    @property
    def design_space(self) -> Optional[DesignSpace]:
        """Get the design space used during the auto configuration steps."""
        return self._design_space

    @property
    def design_workflow(self) -> Optional[DesignWorkflow]:
        """Get the default design workflow, if it was created by this object."""
        return self._design_workflow

    @property
    def design_execution(self) -> Optional[DesignExecution]:
        """Get the design execution, if it was created by this object."""
        return self._design_execution

    @property
    def assets(self):
        """Get all assets configured by this object."""
        initial_assets = [
            self.table_config, self.table, self.predictor,
            self.predictor_evaluation_workflow, self.predictor_evaluation_execution,
            self.design_space, self.design_workflow, self.design_execution
        ]
        return [asset for asset in initial_assets if asset is not None]

    def execute(self, *, score: Score) -> DesignExecution:
        """[ALPHA] Execute a design execution given a provided score.

        A design workflow must be present after auto-configuration to execute the score.
        This method can be called after modifying auto-configured assets
        to create a new, custom design execution.

        Parameters
        ----------
        score: Score
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing in predictor responses.

        """
        if self.design_workflow is None:
            raise ValueError("Design workflow is missing, cannot execute score.")
        execution = self.design_workflow.design_executions.trigger(score)
        self._design_execution = execution
        return self.design_execution

    def from_material(
            self,
            *,
            material: Union[str, UUID, LinkByUID, MaterialRun],
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Score] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
    ):
        """[ALPHA] Auto configure platform assets from material history to design workflow.

        Given a material on the Citrine Platform,
        configures a default GEM table, predictor, design space, and design workflow.

        An optional evaluator, design_space, and score can be provided:
            evaluator    -> A PredictorEvaluator to be used in place of the default
            design_space -> A DesignSpace to be used in place of the default
            score        -> Triggers a design execution from the auto-configured design workflow

        Parameters
        ----------
        material: Union[str, UUID, LinkByUID, MaterialRun]
            A representation of the material to configure a
            default table, predictor, and design space from.
        evaluator: Optional[PredictorEvaluator]
            A PredictorEvaluator to use in place of the default.
            Must contain responses matching outputs of the default predictor.
            Default: None
        design_space: Optional[DesignSpace]
            A DesignSpace object to use in place of the default.
            If not registered already, will be registered during configuration.
            Default: None
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        mode: AutoConfigureMode
            The method to be used in the automatic table and predictor configuration.
            Default: AutoConfigureMode.PLAIN
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False

        """
        if not isinstance(mode, AutoConfigureMode):
            raise TypeError('mode must be an option from AutoConfigureMode')

        # Run table build stage
        self._table_build_stage(material=material, mode=mode)

        # Finish workflow from table stage
        self.from_table(
            table=self.table, score=score, evaluator=evaluator,
            design_space=design_space, mode=mode, print_status_info=print_status_info
        )

    def from_table(
            self,
            *,
            table: GemTable,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Score] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
    ):
        """[ALPHA] Auto configure platform assets from GEM table to design workflow.

        Given a GEM table on the Citrine Platform,
        creates a default predictor, design space, and design workflow.

        An optional evaluator, design_space, and score can be provided:
            evaluator    -> A PredictorEvaluator to be used in place of the default
            design_space -> A DesignSpace to be used in place of the default
            score        -> Triggers a design execution from the auto-configured design workflow

        Parameters
        ----------
        table: Table
            A GEM table to configure a default predictor,
            design space, and design workflow from.
        evaluator: Optional[PredictorEvaluator]
            A PredictorEvaluator to use in place of the default.
            Must contain responses matching outputs of the default predictor.
            Default: None
        design_space: Optional[DesignSpace]
            A DesignSpace object to use in place of the default.
            If not registered already, will be registered during configuration.
            Default: None
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        mode: AutoConfigureMode
            The method to be used in the automatic predictor configuration.
            Default: AutoConfigureMode.PLAIN
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False

        """
        if not isinstance(mode, AutoConfigureMode):
            raise TypeError('mode must be an option from AutoConfigureMode')

        # Run predictor build stage
        self._predictor_build_stage(table=table, mode=mode, print_status_info=print_status_info)

        # Finish workflow from predictor stage
        self.from_predictor(
            predictor=self.predictor, score=score, evaluator=evaluator,
            design_space=design_space, print_status_info=print_status_info
        )

    def from_predictor(
            self,
            *,
            predictor: Predictor,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Score] = None,
            print_status_info: bool = False
    ):
        """[ALPHA] Auto configure platform assets from predictor to design workflow.

        Given a predictor on the Citrine Platform,
        creates a default design space and design workflow.

        An optional evaluator, design_space, and score can be provided:
            evaluator    -> A PredictorEvaluator to be used in place of the default
            design_space -> A DesignSpace to be used in place of the default
            score        -> Triggers a design execution from the auto-configured design workflow

        Parameters
        ----------
        predictor: Predictor
            A registered predictor to configure a default design space and design workflow from.
        evaluator: Optional[PredictorEvaluator]
            A PredictorEvaluator to use in place of the default.
            Must contain responses matching outputs of the default predictor.
            Default: None
        design_space: Optional[DesignSpace]
            A DesignSpace object to use in place of the default.
            If not registered already, will be registered during configuration.
            Default: None
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False

        """
        if predictor.uid is None:
            raise ValueError("Predictor has uid=None. Are you using a registered resource?")

        # Run the predictor evaluation stage
        self._predictor_evaluation_stage(
            predictor=predictor,
            evaluator=evaluator,
            print_status_info=print_status_info
        )

        # Run the design space stage
        self._design_space_build_stage(
            predictor=predictor,
            design_space=design_space,
            print_status_info=print_status_info
        )

        # Run the design workflow build stage, trigger score if provided
        self._design_workflow_build_stage(
            predictor=predictor,
            design_space=self.design_space,  # Use the object from previous stage
            score=score,
            print_status_info=print_status_info
        )

    def _table_build_stage(
            self,
            *,
            material: Union[str, UUID, LinkByUID, MaterialRun],
            mode: AutoConfigureMode
    ):
        """Create a default GEM table from a material."""
        # TODO: package-wide formatting enum for method
        table_algorithm_map = {
            'PLAIN': TableBuildAlgorithm.SINGLE_ROW,
            'FORMULATION': TableBuildAlgorithm.FORMULATIONS
        }
        table_algorithm = table_algorithm_map[mode.value]

        print("Configuring default GEM table from material history...")
        table_config, _ = self.project.table_configs.default_for_material(
            material=material, name=f'{self._prefix}Default GEM Table',
            algorithm=table_algorithm
        )
        table_config = self.project.table_configs.register(table_config)
        table = self.project.tables.build_from_config(table_config)

        self._table_config = table_config
        self._table = table
        self._status = AutoConfigureStatus.TABLE_CREATED

    def _predictor_build_stage(
            self,
            *,
            table: GemTable,
            mode: AutoConfigureMode,
            print_status_info: bool
    ):
        """Create a default predictor from a GEM table."""
        print("Configuring default predictor from GEM table...")
        data_source = GemTableDataSource(table_id=table.uid, table_version=table.version)
        predictor = self.project.predictors.auto_configure(
            training_data=data_source, pattern=mode.value  # Uses same string pattern
        )
        predictor.name = f'{self._prefix}Default Predictor'
        predictor = self.project.predictors.register(predictor)
        predictor = wait_while_validating(
            collection=self.project.predictors, module=predictor,
            print_status_info=print_status_info
        )

        self._predictor = predictor
        self._status = AutoConfigureStatus.PREDICTOR_CREATED
        self._status_info = predictor.status_info

        if predictor.status == 'INVALID':
            self._status = AutoConfigureStatus.PREDICTOR_INVALID
            raise RuntimeError("Predictor is invalid,"
                               " cannot proceed to design space configuration.")

    def _predictor_evaluation_stage(
            self,
            *,
            predictor: Predictor,
            evaluator: Optional[PredictorEvaluator],
            print_status_info: bool
    ):
        """Evaluate the predictor with the specified evaluator, or create a default workflow."""
        print("Configuring predictor evaluation workflow/execution...")
        if evaluator is None:
            # No evaluator, so create a default PEW for the predictor
            pew = self.project.predictor_evaluation_workflows.create_default(
                predictor_id=predictor.uid
            )
        else:
            # We got an evaluator, so make a new PEW and register it manually
            pew = PredictorEvaluationWorkflow(
                name=f'{self._prefix}Predictor Evaluation Workflow',
                evaluators=[evaluator]
            )
            pew = self.project.predictor_evaluation_workflows.register(pew)

        pew = wait_while_validating(
            collection=self.project.predictor_evaluation_workflows, module=pew,
            print_status_info=print_status_info
        )

        self._predictor_evaluation_workflow = pew
        self._status = AutoConfigureStatus.PEW_CREATED
        self._status_info = pew.status_info

        if pew.status == 'FAILED':
            # Can proceed without raising error, but can't get PEE
            self._status = AutoConfigureStatus.PEW_FAILED
            warnings.warn("Predictor evaluation workflow failed -- unable to configure execution.")
        else:
            if evaluator is None:
                # Get execution from default
                # PEE creation occurs soon after validation, short wait for safety
                time.sleep(5)
                self._predictor_evaluation_execution = next(pew.executions.list(), None)
            else:
                # Manually trigger execution
                self._predictor_evaluation_execution = pew.executions.trigger(predictor.uid)

    def _design_space_build_stage(
            self,
            *,
            predictor: Predictor,
            design_space: Optional[DesignSpace],
            print_status_info: bool
    ):
        """Create a design space from a specified predictor, or use the provided one."""
        if design_space is None:
            ds_source = 'predictor'
            design_space = self.project.design_spaces.create_default(predictor_id=predictor.uid)
            design_space.name = f'{self._prefix}Default Design Space'
        else:
            ds_source = 'user input'

        print("Configuring design space from {}...".format(ds_source))
        if design_space.uid is None:
            design_space = self.project.design_spaces.register(design_space)
        design_space = wait_while_validating(
            collection=self.project.design_spaces, module=design_space,
            print_status_info=print_status_info
        )

        self._design_space = design_space
        self._status = AutoConfigureStatus.DESIGN_SPACE_CREATED
        self._status_info = design_space.status_info

        if design_space.status == 'INVALID':
            self._status = AutoConfigureStatus.DESIGN_SPACE_INVALID
            raise RuntimeError("Design space is invalid,"
                               " cannot proceed to design workflow configuration.")

    def _design_workflow_build_stage(
            self,
            *,
            predictor: Predictor,
            design_space: DesignSpace,
            score: Optional[Score],
            print_status_info: bool
    ):
        """Create a design workflow, and optionally trigger a design execution."""
        print("Configuring design workflow for design space...")
        workflow = DesignWorkflow(
            name=f'{self._prefix}Default Design Workflow',
            predictor_id=predictor.uid,
            design_space_id=design_space.uid,
            processor_id=None
        )
        workflow = self.project.design_workflows.register(workflow)
        workflow = wait_while_validating(
            collection=self.project.design_workflows, module=workflow,
            print_status_info=print_status_info
        )

        self._design_workflow = workflow
        self._status = AutoConfigureStatus.DESIGN_WORKFLOW_CREATED
        self._status_info = workflow.status_info

        # TODO: Allow user to provide objective or score
        if workflow.status == 'FAILED':
            self._status = AutoConfigureStatus.DESIGN_WORKFLOW_FAILED
            if score is None:
                print("No score provided to trigger design execution -- finished.")
            else:
                raise RuntimeError("Design workflow validation failed,"
                                   " cannot trigger design execution.")
        elif score is not None:
            print("Triggering design execution using provided score...")
            self.execute(score=score)
