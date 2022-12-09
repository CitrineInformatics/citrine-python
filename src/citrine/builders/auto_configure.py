from logging import getLogger
from uuid import UUID
from typing import Union, Optional, List

from gemd.entity.link_by_uid import LinkByUID
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.seeding.find_or_create import find_collection, create_or_update
from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.executions import DesignExecution
from citrine.informatics.design_candidate import DesignCandidate
from citrine.informatics.design_spaces import DesignSpace
from citrine.informatics.predictor_evaluator import PredictorEvaluator
from citrine.informatics.objectives import Objective
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow, PredictorEvaluationWorkflow

from citrine.resources.gemtables import GemTable
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import Predictor, AutoConfigureMode
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig, TableBuildAlgorithm

from citrine.builders.scores import create_default_score

logger = getLogger(__name__)


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
    design space, and design workflow in a linear fashion,
    starting from a provided material/table/predictor.

    All assets that are registered to the Citrine Platform
    during the auto configuration steps are stored as members of this class.
    In case this method fails during asset validation,
    the previously configured items are accessible
    locally and on the Citrine Platform.

    Initializing an AutoConfigureWorkflow will search for assets
    on the Citrine Platform based on the specified name,
    and re-use/update these items during subsequent runs.
    Currently, assets are searched for by name and type in the project,
    and duplicately named assets will result in an error being thrown.

    Example usage:
    ```
    # Initialize score and workflow
    score = LIScore(objectives=[ScalarMaxObjective(descriptor_key='Desc 1'), baselines=[1.0])
    auto_config = AutoConfigureWorkflow(project=project, name='My Project Name')

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
    design_space = auto_config.design_space
    workflow = auto_config.design_workflow
    ```

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform.
    name: str
        Name to affix to auto-configured assets on the Citrine Platform.
        This name is used as an identifier for finding and re-using
        assets related to a given workflow.

    """

    def __init__(self, *, project: Project, name: str):
        self._project = project
        self._name = name
        self._status = AutoConfigureStatus.START
        self._status_info = []

        # Blank initialize assets
        self._table_config = None
        self._table = None
        self._predictor = None
        self._predictor_evaluation_workflow = None
        self._design_space = None
        self._design_workflow = None
        self._design_execution = None

        separator = ": " if self.name else ""
        self._default_asset_names = {
            "TABLE_CONFIG": f"{self.name}{separator}Auto Configure GEM Table",
            "PREDICTOR": f"{self.name}{separator}Auto Configure Predictor",
            "PEW": f"{self.name}{separator}Auto Configure PEW",
            "DESIGN_SPACE": f"{self.name}{separator}Auto Configure Design Space",
            "DESIGN_WORKFLOW": f"{self.name}{separator}Auto Configure Design Workflow"
        }

        # Search project for current status
        self.update()

    @staticmethod
    def _print_status(msg: str):
        logger.info(f"AutoConfigureWorkflow: {msg}")

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
        """Get the table config associated with this workflow."""
        return self._table_config

    @property
    def table(self) -> Optional[GemTable]:
        """Get the GEM table associated with this workflow."""
        return self._table

    @property
    def predictor(self) -> Optional[Predictor]:
        """Get the predictor associated with this workflow."""
        return self._predictor

    @property
    def predictor_evaluation_workflow(self) -> Optional[PredictorEvaluationWorkflow]:
        """Get the predictor evaluation workflow associated with this workflow."""
        return self._predictor_evaluation_workflow

    @property
    def design_space(self) -> Optional[DesignSpace]:
        """Get the design space associated with this workflow."""
        return self._design_space

    @property
    def design_workflow(self) -> Optional[DesignWorkflow]:
        """Get the design workflow associated with this workflow."""
        return self._design_workflow

    @property
    def design_execution(self) -> Optional[DesignExecution]:
        """Get the most recent design execution from this workflow."""
        return self._design_execution

    @property
    def score(self) -> Optional[Score]:
        """Get the most recent score executed by this workflow."""
        de = self.design_execution
        return de.score if de is not None else None

    @property
    def candidates(self) -> List[DesignCandidate]:
        """Get the candidate list from the most recent design execution."""
        de = self.design_execution
        return list(de.candidates()) if de is not None else []

    @property
    def assets(self):
        """Get all assets configured by this object."""
        initial_assets = [
            self.table_config, self.table, self.predictor,
            self.predictor_evaluation_workflow,
            self.design_space, self.design_workflow,
        ]
        return [asset for asset in initial_assets if asset is not None]

    def update(self):
        """Search for existing assets matching the workflow name and update its status."""
        self._update_assets()
        self._update_status()

    def _update_assets(self):
        """Find and store all assets on the platform matching the workflow name."""
        # Table config
        if self.table_config is None:
            self._table_config = find_collection(
                collection=self.project.table_configs,
                name=self._default_asset_names["TABLE_CONFIG"]
            )
        else:
            self._table_config = self.project.table_configs.get(self.table_config.uid)
            logger.info("Found existing: {}".format(self.table_config))

        # Table
        if self.table is None:
            if self.table_config is not None:
                self._table = next(self.project.tables.list_by_config(self.table_config.uid), None)
                if self.table is not None:
                    logger.info("Found existing: {}".format(self.table))
        else:
            self._table = self.project.tables.get(self.table.uid)
            logger.info("Found existing: {}".format(self.table))

        # Predictor
        if self.predictor is None:
            self._predictor = find_collection(
                collection=self.project.predictors,
                name=self._default_asset_names["PREDICTOR"]
            )
        else:
            self._predictor = self.project.predictors.get(self.predictor.uid)
            logger.info("Found existing: {}".format(self.predictor))

        # PEW
        if self.predictor_evaluation_workflow is None:
            self._predictor_evaluation_workflow = find_collection(
                collection=self.project.predictor_evaluation_workflows,
                name=self._default_asset_names["PEW"]
            )
        else:
            self._predictor_evaluation_workflow = self.project.predictor_evaluation_workflows.get(
                self.predictor_evaluation_workflow.uid
            )
            logger.info("Found existing: {}".format(self.predictor_evaluation_workflow))

        # Design space
        if self.design_space is None:
            self._design_space = find_collection(
                collection=self.project.design_spaces,
                name=self._default_asset_names["DESIGN_SPACE"]
            )
        else:
            self._design_space = self.project.design_spaces.get(self.design_space.uid)
            logger.info("Found existing: {}".format(self.design_space))

        # Design workflow
        if self.design_workflow is None:
            self._design_workflow = find_collection(
                collection=self.project.design_workflows,
                name=self._default_asset_names["DESIGN_WORKFLOW"]
            )
        else:
            self._design_workflow = self.project.design_workflows.get(self.design_workflow.uid)
            logger.info("Found existing: {}".format(self.design_workflow))

    def _update_status(self):
        """Update status info based on currently stored assets."""
        # Work backwards from end of workflow, return early when possible
        if self.design_workflow is not None:
            self._status_info = self.design_workflow.status_info
            if self.design_workflow.failed():
                self._status = AutoConfigureStatus.DESIGN_WORKFLOW_FAILED
            else:
                self._status = AutoConfigureStatus.DESIGN_WORKFLOW_CREATED
            return

        if self.design_space is not None:
            self._status_info = [detail.msg for detail in self.predictor.status_detail]
            if self.design_space.failed():
                self._status = AutoConfigureStatus.DESIGN_SPACE_INVALID
            else:
                self._status = AutoConfigureStatus.DESIGN_SPACE_CREATED
            return

        if self.predictor_evaluation_workflow is not None:
            self._status_info = self.predictor_evaluation_workflow
            if self.predictor_evaluation_workflow.failed():
                self._status = AutoConfigureStatus.PEW_FAILED
            else:
                self._status = AutoConfigureStatus.PEW_CREATED
            return

        if self.predictor is not None:
            self._status_info = [detail.msg for detail in self.predictor.status_detail]
            if self.predictor.failed():
                self._status = AutoConfigureStatus.PREDICTOR_INVALID
            else:
                self._status = AutoConfigureStatus.PREDICTOR_CREATED
            return

        if self.table is not None:
            self._status = AutoConfigureStatus.TABLE_CREATED
            return

        self._status = AutoConfigureStatus.START

    def execute(self, *, score: Union[Score, Objective]) -> DesignExecution:
        """[ALPHA] Execute a design execution using the provided score/objective.

        A design workflow must be present after auto-configuration to execute the score.
        This method can be called after modifying auto-configured assets
        to create a new, custom design execution.

        Parameters
        ----------
        score: Union[Score, Objective]
            A score or objective used to rank candidates during design execution.
            If an objective is passed, a default score is constructed
            by reading the GEM table associated with this workflow
            to extract baseline information.

        Returns
        ----------
        DesignExecution
            The design execution triggered with the provided score/objective.

        """
        if self.design_workflow is None:
            raise ValueError("Design workflow is missing, cannot execute score.")

        if isinstance(score, Objective):
            score = create_default_score(objectives=score, project=self.project, table=self.table)

        self._design_execution = self.design_workflow.design_executions.trigger(score)
        return self.design_execution

    def from_material(
            self,
            *,
            material: Union[str, UUID, LinkByUID, MaterialRun],
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Union[Score, Objective]] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
            prefer_valid: bool = True,
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
        score: Optional[Union[Score, Objective]]
            A score or objective used to rank candidates during design execution.
            If only an objective is passed, a default `LIScore` is constructed
            by reading the GEM table associated with this workflow
            to extract baseline scoring information.
            Default: None
        mode: AutoConfigureMode
            The method to be used in the automatic table and predictor configuration.
            Default: AutoConfigureMode.PLAIN
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False
        prefer_valid: Boolean
            If True, enables filtering of sparse descriptors and trimming of
            excess graph components in attempt to return a default configuration
            that will pass validation.
            Default: True.

        """
        if not isinstance(mode, AutoConfigureMode):
            raise TypeError('mode must be an option from AutoConfigureMode')

        # Run table build stage
        self._table_build_stage(material=material, mode=mode)

        # Finish workflow from table stage
        self.from_table(
            table=self.table, score=score, evaluator=evaluator,
            design_space=design_space, mode=mode, print_status_info=print_status_info,
            prefer_valid=prefer_valid
        )

    def from_table(
            self,
            *,
            table: GemTable,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Union[Score, Objective]] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
            prefer_valid: bool = True,
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
        score: Optional[Union[Score, Objective]]
            A score or objective used to rank candidates during design execution.
            If only an objective is passed, a default `LIScore` is constructed
            by reading the GEM table associated with this workflow
            to extract baseline scoring information.
            Default: None
        mode: AutoConfigureMode
            The method to be used in the automatic predictor configuration.
            Default: AutoConfigureMode.PLAIN
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False
        prefer_valid: Boolean
            If True, enables filtering of sparse descriptors and trimming of
            excess graph components in attempt to return a default configuration
            that will pass validation.
            Default: True.

        """
        if not isinstance(mode, AutoConfigureMode):
            raise TypeError('mode must be an option from AutoConfigureMode')

        self._table = table  # Save here, but cannot force rename w/o config

        # Get default predictor, pass to next stage for registration
        data_source = GemTableDataSource(table_id=table.uid, table_version=table.version)
        predictor = self.project.predictors.create_default(
            training_data=data_source, pattern=mode.value,  # Uses same string pattern
            prefer_valid=prefer_valid
        )

        # Finish workflow from predictor stage
        self.from_predictor(
            predictor=predictor, score=score, evaluator=evaluator,
            design_space=design_space, print_status_info=print_status_info
        )

    def from_predictor(
            self,
            *,
            predictor: Predictor,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DesignSpace] = None,
            score: Optional[Union[Score, Objective]] = None,
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
        score: Optional[Union[Score, Objective]]
            A score or objective used to rank candidates during design execution.
            If only an objective is passed, a default `LIScore` is constructed
            by reading the GEM table associated with this workflow
            to extract baseline scoring information.
            Default: None
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False

        """
        # Run the predictor registration stage
        self._predictor_registration_stage(
            predictor=predictor,
            print_status_info=print_status_info
        )

        # Run the predictor evaluation stage
        self._predictor_evaluation_stage(
            predictor=self.predictor,
            evaluator=evaluator,
            print_status_info=print_status_info
        )

        # Run the design space stage
        self._design_space_build_stage(
            predictor=self.predictor,
            design_space=design_space,
            print_status_info=print_status_info
        )

        # Run the design workflow build stage, trigger score if provided
        self._design_workflow_build_stage(
            predictor=self.predictor,
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
        self._print_status("Configuring GEM table...")

        # TODO: package-wide formatting enum for method
        table_algorithm_map = {
            'PLAIN': TableBuildAlgorithm.SINGLE_ROW,
            'FORMULATION': TableBuildAlgorithm.FORMULATIONS
        }
        table_algorithm = table_algorithm_map[mode.value]

        table_config, _ = self.project.table_configs.default_for_material(
            material=material,
            name=self._default_asset_names["TABLE_CONFIG"],
            algorithm=table_algorithm
        )
        table_config = create_or_update(
            collection=self.project.table_configs,
            resource=table_config
        )

        self._table_config = table_config
        self._table = self.project.tables.build_from_config(self.table_config)
        self._status = AutoConfigureStatus.TABLE_CREATED

    def _predictor_registration_stage(
            self,
            *,
            predictor: Predictor,
            print_status_info: bool
    ):
        """Register and validate a provided predictor."""
        self._print_status("Configuring predictor...")

        predictor.name = self._default_asset_names["PREDICTOR"]
        predictor = create_or_update(
            collection=self.project.predictors,
            resource=predictor
        )
        predictor = wait_while_validating(
            collection=self.project.predictors,
            module=predictor,
            print_status_info=print_status_info
        )

        self._predictor = predictor
        self._status = AutoConfigureStatus.PREDICTOR_CREATED
        self._status_info = [detail.msg for detail in predictor.status_detail]

        if predictor.failed():
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
        self._print_status("Configuring predictor evaluation...")

        if evaluator is None:
            # No evaluator, so create a default PEW for the predictor
            pew = self.project.predictor_evaluation_workflows.create_default(
                predictor_id=predictor.uid
            )
        else:
            # We got an evaluator, so make a new PEW and register it manually
            pew = PredictorEvaluationWorkflow(
                name=self._default_asset_names["PEW"],
                evaluators=[evaluator]
            )
            pew = create_or_update(
                collection=self.project.predictor_evaluation_workflows,
                resource=pew
            )

        pew = wait_while_validating(
            collection=self.project.predictor_evaluation_workflows,
            module=pew,
            print_status_info=print_status_info
        )

        self._predictor_evaluation_workflow = pew
        self._status = AutoConfigureStatus.PEW_CREATED
        self._status_info = pew.status_info

        if pew.failed():
            # Can proceed without raising error, but can't get PEE
            self._status = AutoConfigureStatus.PEW_FAILED
            logger.warning(
                "Predictor evaluation workflow failed -- unable to configure execution."
            )
        elif evaluator is not None:
            # Manually trigger execution
            pew.executions.trigger(predictor.uid)

    def _design_space_build_stage(
            self,
            *,
            predictor: Predictor,
            design_space: Optional[DesignSpace],
            print_status_info: bool
    ):
        """Create a design space from a specified predictor, or use the provided one."""
        self._print_status("Configuring design space...")

        if design_space is None:
            design_space = self.project.design_spaces.create_default(predictor_id=predictor.uid)

        design_space.name = self._default_asset_names["DESIGN_SPACE"]
        design_space = create_or_update(
            collection=self.project.design_spaces,
            resource=design_space
        )
        design_space = wait_while_validating(
            collection=self.project.design_spaces, module=design_space,
            print_status_info=print_status_info
        )

        self._design_space = design_space
        self._status = AutoConfigureStatus.DESIGN_SPACE_CREATED
        self._status_info = [detail.msg for detail in design_space.status_detail]

        if design_space.failed():
            self._status = AutoConfigureStatus.DESIGN_SPACE_INVALID
            raise RuntimeError("Design space is invalid,"
                               " cannot proceed to design workflow configuration.")

    def _design_workflow_build_stage(
            self,
            *,
            predictor: Predictor,
            design_space: DesignSpace,
            score: Optional[Union[Score, Objective]],
            print_status_info: bool
    ):
        """Create a design workflow, and optionally trigger a design execution."""
        self._print_status("Configuring design workflow...")

        processor_id = self.design_workflow.processor_id if self.design_workflow else None
        workflow = DesignWorkflow(
            name=self._default_asset_names["DESIGN_WORKFLOW"],
            predictor_id=predictor.uid,
            design_space_id=design_space.uid,
            processor_id=processor_id
        )
        workflow = create_or_update(
            collection=self.project.design_workflows,
            resource=workflow
        )
        workflow = wait_while_validating(
            collection=self.project.design_workflows, module=workflow,
            print_status_info=print_status_info
        )

        self._design_workflow = workflow
        self._status = AutoConfigureStatus.DESIGN_WORKFLOW_CREATED
        self._status_info = workflow.status_info

        if workflow.failed():
            self._status = AutoConfigureStatus.DESIGN_WORKFLOW_FAILED
            if score is None:
                self._print_status("No score provided to trigger design execution -- finished.")
            else:
                raise RuntimeError("Design workflow validation failed,"
                                   " cannot trigger design execution.")
        elif score is not None:
            self._print_status("Triggering design execution...")
            return self.execute(score=score)
