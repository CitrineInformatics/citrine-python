from uuid import UUID
from typing import Union, List, Optional

from gemd.enumeration.base_enumeration import BaseEnumeration
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.has_property_templates import HasPropertyTemplates
from gemd.entity.template.has_condition_templates import HasConditionTemplates
from gemd.entity.template.has_parameter_templates import HasParameterTemplates
from gemd.util.impl import flatten

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.objectives import Objective
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow

from citrine.resources.material_run import MaterialRun
from citrine.resources.project import Project
from citrine.resources.table_config import TableBuildAlgorithm


class AutoConfigureAlgorithm(BaseEnumeration):
    """[ALPHA] The algorithm to use in building auto-configured assets.

    * PLAIN produces a single-row table and plain predictor
    * FORMULATION produces a multi-row table and formulations predictor
    """

    PLAIN = "plain"
    FORMULATION = "formulation"


def extract_descriptor_keys(
        *,
        project: Project,
        material: Union[str, UUID, LinkByUID, MaterialRun],
        algorithm: AutoConfigureAlgorithm = AutoConfigureAlgorithm.PLAIN,
        full_history: bool = False
) -> List[str]:
    """[ALPHA] Extract names of attributes from a provided material run.

    Given a material run (or ID representation),
    extracts the names of property, condition, and parameter templates
    that appear throughout the material's history.

    The obtained descriptor keys can be used when constructing
    objectives for a scoring function in a design workflow.

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform.
    material: Union[str, UUID, LinkByUID, MaterialRun]
        A representation of the material to extract descriptor keys from its history.
    algorithm: AutoConfigureAlgorithm
        The algorithm to be used in the automatic table and predictor configuration.
        Controls descriptor key formatting to match the configured table columns.
        Default: AutoConfigureAlgorithm.PLAIN
    full_history: bool
        Whether to extract descriptor keys from the full material history,
        or only the provided (terminal) material.
        Default: True

    Returns
    -------
    list
        List of extracted keys from the material history

    """
    if not isinstance(algorithm, AutoConfigureAlgorithm):
        raise TypeError('algorithm must be an option from AutoConfigureAlgorithm')

    # Full history not needed when full_history = False
    # But is convenient to populate templates for terminal material
    history = project.material_runs.get_history(id=material)
    if full_history:
        search_history = flatten(history)
    else:
        # Limit the search to contain the terminal material/process/measurements
        search_history = [history.spec.template, history.process.template]
        search_history.extend([msr.template for msr in history.measurements])

    properties = []
    conditions = []
    parameters = []
    for obj in search_history:
        parent_name = f'{obj.name}~' if algorithm.value == 'plain' else ''
        # Search all attribute template types
        if isinstance(obj, HasPropertyTemplates):
            for property in obj.properties:
                properties.append(parent_name + property[0].name)
        if isinstance(obj, HasConditionTemplates):
            for condition in obj.conditions:
                conditions.append(parent_name + condition[0].name)
        if isinstance(obj, HasParameterTemplates):
            for parameter in obj.parameters:
                parameters.append(parent_name + parameter[0].name)

    return properties + conditions + parameters


def auto_configure_material(
        *,
        project: Project,
        material: Union[str, UUID, LinkByUID, MaterialRun],
        score: Score,
        algorithm: AutoConfigureAlgorithm = AutoConfigureAlgorithm.PLAIN,
        label: str = '',
        print_status_info: bool = False,
) -> DesignExecution:
    """[ALPHA] Auto configures platform assets from GEM table to design execution.

    Given a material run (or ID representation),
    configures and validates a default GEM table, default predictor, and default design space,
    and then triggers a design execution given the provided `score`.

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
    algorithm: AutoConfigureAlgorithm
        The algorithm to be used in the automatic table and predictor configuration.
        Default: AutoConfigureAlgorithm.PLAIN
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

    if not isinstance(algorithm, AutoConfigureAlgorithm):
        raise TypeError('algorithm must be an option from AutoConfigureAlgorithm')

    # Map algorithm to appropriate TableBuildAlgorithm
    if algorithm == AutoConfigureAlgorithm.PLAIN:
        table_algorithm = TableBuildAlgorithm.SINGLE_ROW
    else:
        table_algorithm = TableBuildAlgorithm.FORMULATIONS

    print('Building default GEM table from material history...')
    table_config, _ = project.table_configs.default_for_material(
        material=material, name=f'{prefix}Default GEM Table', algorithm=table_algorithm
    )
    table_config = project.table_configs.register(table_config)
    table = project.tables.build_from_config(table_config)

    print('Building default predictor from GEM table...')
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

    print('Building default design space from predictor...')
    design_space = project.design_spaces.create_default(predictor_id=predictor.uid)
    design_space.name = f'{prefix}Default Design Space'
    design_space = project.design_spaces.register(design_space)
    design_space = wait_while_validating(
        collection=project.design_spaces, module=design_space, print_status_info=print_status_info
    )

    if design_space.status == 'INVALID':
        raise RuntimeError('Auto-configured design space is invalid.')

    print("Building design workflow for design space...")
    workflow = DesignWorkflow(
        name=f'{prefix}Default Design Workflow',
        predictor_id=predictor.uid,
        design_space_id=design_space.uid,
        process_id=None
    )
    workflow = project.design_workflows.register(workflow)
    workflow = wait_while_validating(
        collection=project.design_workflows, module=workflow, print_status_info=print_status_info
    )

    if workflow.status == 'INVALID':
        raise RuntimeError('Auto-configured design workflow is invalid.')

    print("Executing design workflow using provided score...")
    execution = workflow.design_executions.trigger(score)
    return execution
