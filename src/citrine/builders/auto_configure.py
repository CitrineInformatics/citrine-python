from uuid import UUID
from typing import Union, Optional

from gemd.entity.link_by_uid import LinkByUID
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.executions import DesignExecution, PredictorEvaluationExecution
from citrine.informatics.design_spaces import DesignSpace, DataSourceDesignSpace
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

    PLAIN = "plain"
    FORMULATION = "formulation"


class AutoConfigureWorkflow():
    """[ALPHA] Helper class for configuring and storing default assets on the Citrine Platform.

    Defines methods for creating a default GEM table, predictor,
    design space, design workflow, and design execution in a linear fashion,
    starting from a provided material/table/predictor.

    All assets that are registered to the Citrine Platform
    during the auto configuration steps are stored as members of this class.
    In the case that this method fails during asset validation,
    the previously configured items are still accessible
    locally and on the Citrine Platform for later use or modification.

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
        self._prefix = '{} - '.format(name) if name else ''

        # Blank initialize assets
        self._table_config = None
        self._table = None
        self._predictor = None
        self._predictor_evaluation_workflow = None
        self._predictor_evaluation_execution = None
        self._design_space = None
        self._desing_workflow = None
        self._design_execution = None

    @property
    def project(self) -> Project:
        """Get the project used when automatically configuring assets."""
        return self._project

    @property
    def prefix(self) -> str:
        """Get the prefix attached to auto-configured assets."""
        return self._prefix

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
        return self._desing_workflow

    @property
    def design_execution(self) -> Optional[DesignExecution]:
        """Get the design execution, if it was created by this object."""
        return self._design_execution

    @property
    def assets(self):
        """Get all assets created by this object."""
        initial_assets = [
            self.table, self.predictor,
            self.design_space, self.design_workflow, self.design_execution
        ]
        return [asset for asset in initial_assets if asset is not None]

    def from_material(
            self,
            *,
            material: Union[str, UUID, LinkByUID, MaterialRun],
            score: Optional[Score] = None,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DataSourceDesignSpace] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
    ):
        """[ALPHA] Auto configure platform assets from material history to design workflow.

        Given a material on the Citrine Platform,
        configures a default GEM table, predictor, design space, and design workflow.
        If a score is specified, triggers the auto-configured design workflow
        to yield a design execution.

        Optionally, a custom DataSourceDesignSpace can be specified
        by the design_space argument to use in place of the default.

        Results from the default predictor can be evaluated
        by providing an appropriate PredictorEvaluator to the method.

        material: Union[str, UUID, LinkByUID, MaterialRun]
            A representation of the material to configure a
            default table, predictor, and design space from.
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        evaluator: Optional[PredictorEvaluator]
            Predictor evaluator used during the auto configuration workflow.
            Must contain responses with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        design_space: Optional[DataSourceDesignSpace]
            A data source design space to use in place of the default design space.
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

        # Map to appropriate TableBuildAlgorithm
        # TODO: package-wide formatting enum for all auto-config methods
        if mode == AutoConfigureMode.PLAIN:
            table_algorithm = TableBuildAlgorithm.SINGLE_ROW
        else:
            table_algorithm = TableBuildAlgorithm.FORMULATIONS

        print("Configuring default GEM table from material history...")
        table_config, _ = self.project.table_configs.default_for_material(
            material=material, name=f'{self.prefix}Default GEM Table',
            algorithm=table_algorithm
        )
        table_config = self.project.table_configs.register(table_config)
        table = self.project.tables.build_from_config(table_config)
        self._table_config = table_config
        self._table = table

        # Finish workflow from table stage
        self.from_table(
            table=table, score=score, evaluator=evaluator,
            design_space=design_space, mode=mode, print_status_info=print_status_info
        )

    def from_table(
            self,
            *,
            table: GemTable,
            score: Optional[Score] = None,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DataSourceDesignSpace] = None,
            mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
            print_status_info: bool = False,
    ):
        """[ALPHA] Auto configure platform assets from GEM table to design workflow.

        Given a GEM table on the Citrine Platform,
        creates a defaul predictor, design space, and design workflow.
        If a score is specified, triggers the auto-configured design workflow
        to yield a design execution.

        Optionally, a custom DataSourceDesignSpace can be specified
        by the design_space argument to use in place of the default.

        Results from the default predictor can be evaluated
        by providing an appropriate PredictorEvaluator to the method.

        table: Table
            A GEM table to configure a default predictor,
            design space, and design workflow from.
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within column defintions of the provided table.
            Default: None
        evaluator: Optional[PredictorEvaluator]
            Predictor evaluator used during the auto configuration workflow.
            Must contain responses with matching descriptor keys
            to those appearing within column defintions of the provided table.
            Default: None
        design_space: Optional[DataSourceDesignSpace]
            A data source design space to use in place of the default design space.
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

        print("Configuring default predictor from GEM table...")
        data_source = GemTableDataSource(table_id=table.uid, table_version=table.version)
        predictor = self.project.predictors.auto_configure(
            training_data=data_source, pattern=mode.value.upper()  # Uses same string pattern
        )
        predictor.name = f'{self.prefix}Default Predictor'
        predictor = self.project.predictors.register(predictor)
        predictor = wait_while_validating(
            collection=self.project.predictors,
            module=predictor, print_status_info=print_status_info
        )
        self._predictor = predictor

        if predictor.status == 'INVALID':
            raise RuntimeError("Predictor is invalid,"
                               " cannot proceed to design space configuration.")

        # Finish workflow from predictor stage
        self.from_predictor(
            predictor=predictor, score=score, evaluator=evaluator,
            design_space=design_space, print_status_info=print_status_info
        )

    def from_predictor(
            self,
            *,
            predictor: Predictor,
            score: Optional[Score] = None,
            evaluator: Optional[PredictorEvaluator] = None,
            design_space: Optional[DataSourceDesignSpace] = None,
            print_status_info: bool = False
    ):
        """[ALPHA] Auto configure platform assets from predictor to design workflow.

        Given a predictor on the Citrine Platform,
        creates a defaul design space and design workflow.
        If a score is specified, triggers the auto-configured design workflow
        to yield a design execution.

        Optionally, a custom DataSourceDesignSpace can be specified
        by the design_space argument to use in place of the default.

        Results from the default predictor can be evaluated
        by providing an appropriate evaluator to the method.

        predictor: Predictor
            A predictor to configure a default design space and design workflow from.
        score: Optional[Score]
            Scoring function used to rank candidates during design execution.
            Must contain objectives/constraints with matching descriptor keys
            to those appearing within the provided material history.
            Default: None
        evaluator: Optional[PredictorEvaluator]
            Predictor evaluator used during the auto configuration workflow.
            Must contain responses with matching descriptor keys
            to those appearing within the specified predictor.
            Default: None
        design_space: Optional[DataSourceDesignSpace]
            A DataSourceDesignSpace to use in place of the default design space.
            Default: None
        mode: AutoConfigureMode
            The method to be used in the automatic table and predictor configuration.
            Default: AutoConfigureMode.PLAIN
        print_status_info: bool
            Whether to print the status info during validation of assets.
            Default: False

        """
        if evaluator is not None:
            pew = PredictorEvaluationWorkflow(
                name=f'{self.prefix}Predictor Evaluation',
                evaluators=[evaluator]
            )
            print("Registering predictor evaluation workflow using provided evaluator...")
            pew = self.project.predictor_evaluation_workflows.register(pew)
            pew = wait_while_validating(
                collection=self.project.predictor_evaluation_workflows,
                module=pew, print_status_info=print_status_info
            )
            pee = pew.executions.trigger(predictor.uid)  # No need to wait while executing
            self._predictor_evaluation_workflow = pew
            self._predictor_evaluation_execution = pee

        if design_space is None:
            print("Configuring default design space from predictor...")
            design_space = self.project.design_spaces.create_default(predictor_id=predictor.uid)
            design_space.name = f'{self.prefix}Default Design Space'
        else:
            if not isinstance(design_space, DataSourceDesignSpace):
                raise TypeError("User-provided design space must be a DataSourceDesignSpace.")
            print("Registering user-provided design space...")
        design_space = self.project.design_spaces.register(design_space)
        design_space = wait_while_validating(
            collection=self.project.design_spaces,
            module=design_space, print_status_info=print_status_info
        )

        self._design_space = design_space

        if design_space.status == 'INVALID':
            raise RuntimeError("Design space is invalid,"
                               " cannot proceed to design workflow configuration.")

        print("Configuring design workflow for design space...")
        workflow = DesignWorkflow(
            name=f'{self.prefix}Default Design Workflow',
            predictor_id=predictor.uid,
            design_space_id=design_space.uid,
            processor_id=None
        )
        workflow = self.project.design_workflows.register(workflow)
        workflow = wait_while_validating(
            collection=self.project.design_workflows, module=workflow,
            print_status_info=print_status_info
        )
        self._desing_workflow = workflow

        if score is not None:
            if workflow.status == 'FAILED':
                raise RuntimeError("Design workflow is invalid,"
                                   " cannot trigger design execution.")

            print("Triggering design execution using provided score...")
            execution = workflow.design_executions.trigger(score)
            self._design_execution = execution
