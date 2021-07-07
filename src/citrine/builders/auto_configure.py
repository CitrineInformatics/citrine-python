from uuid import UUID
from typing import Union

from gemd.entity.link_by_uid import LinkByUID

from citrine.jobs.waiting import wait_while_validating
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.executions.design_execution import DesignExecution
from citrine.informatics.scores import Score
from citrine.informatics.workflows import DesignWorkflow

from citrine.resources.data_concepts import _make_link_by_uid
from citrine.resources.material_run import MaterialRun
from citrine.resources.project import Project
from citrine.resources.table_config import TableBuildAlgorithm


def guess_descriptor_keys(
        *,
        project: Project,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        mode: str = 'SIMPLE'
):
    """
    Try to figure out the keys of descriptors that can be used
    as an objective function for this material history.

    """
    if mode not in {"FORMULATION", "SIMPLE"}:
        msg = "Called with mode: {}.  Expected 'FORMULATION' or 'SIMPLE'.".format(mode)
        raise ValueError(msg)

    link = _make_link_by_uid(material)
    history = project.material_runs.get_history(scope=link.scope, id=link.id)

    keys = []
    for msr in history.measurements:
        for prop in msr.properties:
            descriptor_key = f'{msr.name}~{prop.name}' if mode == 'SIMPLE' else prop.name
            keys.append(descriptor_key)

    return  keys

def auto_configure_material(
        *,
        project: Project,
        material: Union[MaterialRun, LinkByUID, str, UUID],
        score: Score,
        mode: str = 'SIMPLE',
        label: str = '',
        print_status_info: bool = False,
) -> DesignExecution:
    """
    Material --> GEMTable --> Predictor --> Design Space --> Design Workflow --> Execution

    """
    if mode not in {"FORMULATION", "SIMPLE"}:
        msg = "Called with mode: {}.  Expected 'FORMULATION' or 'SIMPLE'.".format(mode)
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
    job = project.tables.initiate_build(table_config)
    table = project.tables.get_by_build_job(job)

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
    execution = design_workflow.design_executions.trigger(score)
    return execution
