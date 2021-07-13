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

from citrine.resources.material_run import MaterialRun
from citrine.resources.project import Project
from citrine.resources.table_config import TableBuildAlgorithm


def auto_configure_material(
        *,
        project: Project,
        material: Union[str, UUID, LinkByUID, MaterialRun],
        score: Score,
        algorithm: AutoConfigureMode = AutoConfigureMode.PLAIN,
        design_space: Optional[DataSourceDesignSpace] = None,
        label: str = '',
        print_status_info: bool = False,
) -> DesignExecution:
    """[ALPHA] Auto configures platform assets from GEM table to design execution.

    Given a material run (or ID representation),
    configures and validates a default GEM table, default predictor, and default design space,
    and then triggers a design execution given the provided `score`.

    Optionally, a `DataSourceDesignSpace` can be provided by
    the `design_space` keyword argument to use in place of
    the default configured design space.

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform.
    material: Union[str, UUID, LinkByUID, MaterialRun],
        A representation of the material to a configure a
        default table, predictor, and design space from.
    score: Score
        Scoring function used to rank candidates during design execution.
        Must contain objectives/constraints with matching descriptor keys
        to those appearing within the provided material history.
        Default: None
    mode: AutoConfigureMode
        The algorithm to be used in the automatic table and predictor configuration.
        Default: AutoConfigureMode.PLAIN
    design_space: Optional[DataSourceDesignSpace]
        A data source design space to use in place of the default design space.
        Default: None
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
    prefix = '{} - '.format(label) if label else ''

    if not isinstance(mode, AutoConfigureMode):
        raise TypeError('mode must be an option from AutoConfigureMode')

    # Map algorithm to appropriate TableBuildAlgorithm
    if mode == AutoConfigureMode.PLAIN:
        table_algorithm = TableBuildAlgorithm.SINGLE_ROW
    else:
        table_algorithm = TableBuildAlgorithm.FORMULATIONS

    print('Building default GEM table from material history...')
    table_config, _ = project.table_configs.default_for_material(
        material=material, name=f'{prefix}Default GEM Table', algorithm=table_algorithm
    )
    table_config = project.table_configs.register(table_config)
    table = project.tables.build_from_config(table_config)

    print('\nBuilding default predictor from GEM table...')
    data_source = GemTableDataSource(table_id=table.uid, table_version=table.version)
    predictor = project.predictors.auto_configure(
        training_data=data_source, pattern=algorithm.value.upper()  # Uses same string pattern
    )
    predictor.name = f'{prefix}Default Predictor'
    predictor = project.predictors.register(predictor)
    predictor = wait_while_validating(
        collection=project.predictors, module=predictor, print_status_info=print_status_info
    )

    if predictor.status == 'INVALID':
        raise RuntimeError('Auto-configured predictor is invalid.')

    if design_space is None:
        print('\nBuilding default design space from predictor...')
        design_space = project.design_spaces.create_default(predictor_id=predictor.uid)
        design_space.name = f'{prefix}Default Design Space'
    else:
        if not isinstance(design_space, DataSourceDesignSpace):
            raise TypeError('User provided design space must be a DataSourceDesignSpace.')
        print('\nRegistering user provided design space...')
    design_space = project.design_spaces.register(design_space)
    design_space = wait_while_validating(
        collection=project.design_spaces, module=design_space, print_status_info=print_status_info
    )

    if design_space.status == 'INVALID':
        raise RuntimeError('Auto-configured design space is invalid.')

    print("\nBuilding design workflow for design space...")
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

    if workflow.status == 'INVALID':
        raise RuntimeError('Auto-configured design workflow is invalid.')

    print("\nTriggering design execution using provided score...")
    execution = workflow.design_executions.trigger(score)
    return execution
