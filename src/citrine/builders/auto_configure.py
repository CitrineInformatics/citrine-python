from uuid import UUID
from typing import Union, List, Optional

from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.has_property_templates import HasPropertyTemplates
from gemd.entity.template.has_condition_templates import HasConditionTemplates
from gemd.entity.template.has_parameter_templates import HasParameterTemplates
from gemd.util.impl import flatten

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.design_spaces import DataSourceDesignSpace
from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow

from citrine.resources.gemtables import GemTable
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import Predictor
from citrine.resources.project import Project
from citrine.resources.table_config import TableBuildAlgorithm

from citrine.builders import AutoConfigureMode


def auto_configure_candidates(
        *,
        project: Project,
        score: Score,
        material: Optional[Union[str, UUID, LinkByUID, MaterialRun]] = None,
        table: Optional[GemTable] = None,
        predictor: Optional[Predictor] = None,
        design_space: Optional[DataSourceDesignSpace] = None,
        mode: AutoConfigureMode = AutoConfigureMode.PLAIN,
        label: str = '',
        print_status_info: bool = False,
) -> DesignExecution:
    """[ALPHA] Auto configure platform assets from GEM table to design execution.

    If a `material` is specified as input,
    a default GEM table, predictor, and design space is configured,
    and a design execution is triggered given the provided `score`.
    If a `table` is specified as input,
    a `material` is not required and creation of the default GEM table is skipped.
    If a `predictor` is specified as input,
    neither a `material` or `table` is required,
    and the creation of both a default GEM table and predictor is skipped.

    Optionally, a `DataSourceDesignSpace` can be provided in
    the `design_space` argument to use in place of
    the default configured design space.

    The validation of platform assets is dependent
    on the validity of any previous steps in the workflow.
    In the case that asset validation fails at an intermediate step in this workflow,
    auto-configured assets can still be accessed on the Citrine Platform
    for further use.

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform.
    score: Score
        Scoring function used to rank candidates during design execution.
        Must contain objectives/constraints with matching descriptor keys
        to those appearing within the provided material history.
    material: Optional[Union[str, UUID, LinkByUID, MaterialRun]],
        A representation of the material to a configure a
        default table, predictor, and design space from.
        Only required if not specifying a table or predictor.
        Default: None
    table: Optional[GemTable]
        A GemTable to be used in place of the auto-configured table.
        If specified, a material is not required.
        Default: None
    predictor: Optional[Predictor]
        A Predictor to be used in place of the auto-configured predictor.
        If specified, a material and table are not required.
        Default: None
    design_space: Optional[DataSourceDesignSpace]
        A data source design space to use in place of the default design space.
        Default: None
    mode: AutoConfigureMode
        The method to be used in the automatic table and predictor configuration.
        Default: AutoConfigureMode.PLAIN
    label: str
        Naming label to affix to auto-configured assets on the Citrine Platform.
        Default: ''
    print_status_info: bool
        Whether to print the status of predictor, design space, and design workflow validation.
        Default: False

    Returns
    -------
    DesignExecution
        Triggered design execution given the auto-configured workflow and provided `score`.

    """
    # Make sure we get at least one valid option
    if material is None and table is None and predictor is None:
        raise ValueError("Must specify either a material, table, or predictor.")

    # We don't use this when the predictor is provided
    if predictor is None and not isinstance(mode, AutoConfigureMode):
        raise TypeError("mode must be an option from AutoConfigureMode")

    prefix = '{} - '.format(label) if label else ''

    # Build a GemTable from the specified material
    if table is None and predictor is None:
        # Map to appropriate TableBuildAlgorithm
        # TODO: package-wide formatting enum for all auto-config methods
        if mode == AutoConfigureMode.PLAIN:
            table_algorithm = TableBuildAlgorithm.SINGLE_ROW
        else:
            table_algorithm = TableBuildAlgorithm.FORMULATIONS

        print("Building default GEM table from material history...")
        table_config, _ = project.table_configs.default_for_material(
            material=material, name=f'{prefix}Default GEM Table', algorithm=table_algorithm
        )
        table_config = project.table_configs.register(table_config)
        table = project.tables.build_from_config(table_config)
    elif predictor is None:
        print("Using user-provided GemTable.")

    # Create a default predictor given the table
    if predictor is None:
        print("Building default predictor from GEM table...")
        data_source = GemTableDataSource(table_id=table.uid, table_version=table.version)
        predictor = project.predictors.auto_configure(
            training_data=data_source, pattern=mode.value.upper()  # Uses same string pattern
        )
        predictor.name = f'{prefix}Default Predictor'
        predictor = project.predictors.register(predictor)
    else:
        # They gave us a predictor, make sure it's registered
        print("Using user-provided predictor: {}.".format(predictor.name))
        if predictor.uid is None:
            predictor = project.predictors.register(predictor)

    # Wait while validating, regardless of how we got it
    predictor = wait_while_validating(
        collection=project.predictors, module=predictor, print_status_info=print_status_info
    )
    if predictor.status == 'INVALID':
        raise RuntimeError("Predictor is invalid, cannot proceed to design space.")

    if design_space is None:
        print("Building default design space from predictor...")
        design_space = project.design_spaces.create_default(predictor_id=predictor.uid)
        design_space.name = f'{prefix}Default Design Space'
    else:
        if not isinstance(design_space, DataSourceDesignSpace):
            raise TypeError("User provided design space must be a DataSourceDesignSpace.")
        print("Registering user provided design space...")
    design_space = project.design_spaces.register(design_space)
    design_space = wait_while_validating(
        collection=project.design_spaces, module=design_space, print_status_info=print_status_info
    )
    if design_space.status == 'INVALID':
        raise RuntimeError("Design space is invalid, cannot proceed to design workflow.")

    print("Building design workflow for design space...")
    workflow = DesignWorkflow(
        name=f'{prefix}Default Design Workflow',
        predictor_id=predictor.uid,
        design_space_id=design_space.uid,
        processor_id=None
    )
    workflow = project.design_workflows.register(workflow)
    workflow = wait_while_validating(
        collection=project.design_workflows, module=workflow, print_status_info=print_status_info
    )
    if workflow.status == 'FAILED':
        raise RuntimeError("Design workflow is invalid, cannot trigger design execution.")

    print("Triggering design execution using provided score...")
    execution = workflow.design_executions.trigger(score)
    return execution
