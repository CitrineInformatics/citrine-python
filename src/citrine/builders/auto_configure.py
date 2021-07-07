from uuid import UUID
from typing import Union, Dict

from gemd.entity.link_by_uid import LinkByUID
from gemd.util.impl import flatten

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow

from citrine.resources.data_concepts import _make_link_by_uid
from citrine.resources.material_run import MaterialRun
from citrine.resources.measurement_template import MeasurementTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.project import Project
from citrine.resources.table_config import TableBuildAlgorithm


def extract_descriptor_keys(
        *,
        project: Project,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        mode: str = 'SIMPLE',
        full_history: bool = False
) -> Dict:
    """[ALPHA] Extract names of properties and conditions that appear within
    a provided material history to use as descriptor keys.

    Given a material (or link representation), extracts the names from
    property and condition templates that appear within process and measurement runs
    throughout the material's history.

    The obtained descriptor keys can be used when constructing
    objectives for a scoring function in a design workflow.

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform
    material: Union[MaterialRun, LinkByUID, str, UUID]
        Sample material to extract descriptor keys
    mode: str
        Option in {'SIMPLE', 'FORMULATION'} that controls formatting descriptor keys
        Default: 'SIMPLE'
    full_history: bool
        Whether to extract descriptor keys from the full material history,
        or only the provided (terminal) material
        Default: True

    Returns
    -------
    dict
        {'conditions': [...], 'properties': [...]} dictionary containing descriptor keys

    """
    if mode not in {"FORMULATION", "SIMPLE"}:
        msg = "Called with mode: {}.  Expected 'SIMPLE' or 'FORMULATION'.".format(mode)
        raise ValueError(msg)

    link = _make_link_by_uid(material)
    history = project.material_runs.get_history(scope=link.scope, id=link.id)

    if full_history:
        search_history = flatten(history)
    else:
        # Limit the history to contain the terminal measurement/process
        search_history = [msr.template for msr in history.measurements]
        search_history += [history.process.template]

    keys = {'properties': [], 'conditions': []}
    for obj in search_history:
        if isinstance(obj, (ProcessTemplate, MeasurementTemplate)):
            parent_name = f'{obj.name}~' if mode == 'SIMPLE' else ''
            if isinstance(obj, MeasurementTemplate):
                for prop in obj.properties:
                    property_key = parent_name + prop[0].name
                    keys['properties'].append(property_key)
            for condition in obj.conditions:
                condition_key = parent_name + condition[0].name
                keys['conditions'].append(condition_key)

    return keys


def material_to_candidates(
        *,
        project: Project,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        score: Score,
        mode: str = 'SIMPLE',
        label: str = '',
        print_status_info: bool = False,
) -> DesignExecution:
    """[ALPHA]

    Parameters
    ----------
    project: Project
        Project to use when accessing the Citrine Platform
    material: Union[MaterialRun, LinkByUID, str, UUID]
        Sample material to extract descriptor keys
    score: Score
        Scoring function used to rank candidates during design execution.
        Must contain objectives/constraints with matching descriptor keys
        to those found within the provided material history.
    mode: str
        Option in {'SIMPLE', 'FORMULATION'} that controls formatting descriptor keys
        Default: 'SIMPLE'
    label: str
        Naming label to affix to auto-configured assets on the Citrine Platform
        Default: ''
    print_status_info: bool
        Whether to print the status of predictor, design space, and design workflow validation
        Default: False

    Returns
    -------
    DesignExecution
        Triggered design execution given the auto-configured workflow and provided `score`

    """
    if mode not in {"FORMULATION", "SIMPLE"}:
        msg = "Called with mode: {}.  Expected 'SIMPLE' or 'FORMULATION'.".format(mode)
        raise ValueError(msg)

    suffix = ' - {}'.format(label) if label else ''

    # Mapping of input mode to the config input options (different for each case)
    config_options = {
        'FORMULATION': (TableBuildAlgorithm.FORMULATIONS, 'FORMULATION'),
        'SIMPLE': (TableBuildAlgorithm.SINGLE_ROW, 'PLAIN')
    }
    table_algorithm, predictor_pattern = config_options[mode]

    print('Building default GEM table from material history...')
    table_config, _ = project.table_configs.default_for_material(
        material=material, name=f'Default GEM Table{suffix}', algorithm=table_algorithm
    )
    table_config = project.table_configs.register(table_config)
    table = project.tables.build_from_config(table_config)

    print('Building default predictor from GEM table...')
    formulation = None
    if mode == 'FORMULATION':
        formulation = FormulationDescriptor('Formulation descriptor')
    data_source = GemTableDataSource(
        table_id=table.uid, table_version=table.version, formulation_descriptor=formulation
    )

    predictor = project.predictors.auto_configure(
        training_data=data_source, pattern=predictor_pattern
    )
    predictor.name = f'Default Predictor{suffix}'
    predictor = project.predictors.register(predictor)
    predictor = wait_while_validating(
        collection=project.predictors, module=predictor, print_status_info=print_status_info
    )

    print('Building default design space from predictor...')
    design_space = project.design_spaces.create_default(predictor_id=predictor.uid)
    design_space.name = f'Default Design Space{suffix}'
    design_space = project.design_spaces.register(design_space)
    design_space = wait_while_validating(
        collection=project.design_spaces, module=design_space, print_status_info=print_status_info
    )

    print("Building design workflow for design space...")
    workflow = DesignWorkflow(name=f'Design Workflow{suffix}', predictor_id=predictor.uid,
                              design_space_id=design_space.uid, processor_id=None)
    workflow = project.design_workflows.register(workflow)
    workflow = wait_while_validating(
        collection=project.design_workflows, module=workflow, print_status_info=print_status_info
    )

    print("Executing design workflow using provided score...")
    execution = workflow.design_executions.trigger(score)
    return execution
