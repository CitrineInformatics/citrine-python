import random
import uuid
from copy import deepcopy

import pytest

from citrine.informatics.predictors import AutoMLEstimator
from citrine.resources.status_detail import StatusDetail, StatusLevelEnum
from tests.utils.factories import (PredictorEntityDataFactory, PredictorDataDataFactory,
                                   PredictorMetadataDataFactory, StatusDataFactory)


def build_predictor_entity(instance, status_name="READY", status_detail=[]):
    user = str(uuid.uuid4())
    time = '2020-04-23T15:46:26Z'
    return dict(
        id=str(uuid.uuid4()),
        data=dict(
            name=instance.get("name"),
            description=instance.get("description"),
            instance=instance
        ),
        metadata=dict(
            status=dict(
                name=status_name,
                detail=status_detail
            ),
            created=dict(
                user=user,
                time=time
            ),
            updated=dict(
                user=user,
                time=time
            )
        )
    )


@pytest.fixture
def valid_product_design_space_data():
    """Produce valid product design space data."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_detail=[],
        archived=False,
        display_name='my design space',
        id=str(uuid.uuid4()),
        config=dict(
            type='ProductDesignSpace',
            name='my design space',
            description='does some things',
            subspaces=[
                dict(
                    module_type='DESIGN_SPACE',
                    status='READY',
                    status_detail=[],
                    id=str(uuid.uuid4()),
                    archived=False,
                    name='first subspace',
                    instance=dict(
                        type='FormulationDesignSpace',
                        name='first subspace',
                        description='',
                        formulation_descriptor=FormulationDescriptor.hierarchical().dump(),
                        ingredients=['foo'],
                        labels={'bar': ['foo']},
                        constraints=[],
                        resolution=0.1
                    )
                ),
                dict(
                    module_type='DESIGN_SPACE',
                    status='CREATED',
                    status_detail=[],
                    id=None,
                    archived=False,
                    name='second subspace',
                    instance=dict(
                        type='FormulationDesignSpace',
                        name='second subspace',
                        description='formulates some things',
                        formulation_descriptor=FormulationDescriptor.hierarchical().dump(),
                        ingredients=['baz'],
                        labels={},
                        constraints=[],
                        resolution=0.1
                    )
                )
            ],
            dimensions=[
                dict(
                    type='ContinuousDimension',
                    descriptor=dict(
                        type='Real',
                        descriptor_key='alpha',
                        units='',
                        lower_bound=5.0,
                        upper_bound=10.0,
                    ),
                    lower_bound=6.0,
                    upper_bound=7.0
                ),
                dict(
                    type='EnumeratedDimension',
                    descriptor=dict(
                        type='Categorical',
                        descriptor_key='color',
                        descriptor_values=['blue', 'green', 'red'],
                    ),
                    list=['red']
                )
            ]
        )
    )


@pytest.fixture
def old_valid_product_design_space_data(valid_product_design_space_data):
    """Produce old valid product design space data (no subspaces, different type hint)."""
    ret = deepcopy(valid_product_design_space_data)
    del ret['config']['subspaces']
    ret['config']['type'] = 'Univariate'
    return ret


@pytest.fixture
def valid_enumerated_design_space_data():
    """Produce valid enumerated design space data."""
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_detail=[],
        archived=True,
        display_name='my enumerated design space',
        id=str(uuid.uuid4()),
        config=dict(
            type='EnumeratedDesignSpace',
            name='my enumerated design space',
            description='enumerates some things',
            descriptors=[
                dict(
                    type='Real',
                    descriptor_key='x',
                    units='',
                    lower_bound=1.0,
                    upper_bound=2.0,
                ),
                dict(
                    type='Categorical',
                    descriptor_key='color',
                    descriptor_values=['blue', 'green', 'red'],
                ),
                dict(
                    type='Inorganic',
                    descriptor_key='formula'
                )
            ],
            data=[
                dict(x=1, color='red', formula='C44H54Si2'),
                dict(x=2.0, color='green', formula='V2O3')
            ]
        )
    )



@pytest.fixture
def valid_formulation_design_space_data():
    """Produce valid formulation design space data."""
    from citrine.informatics.constraints import IngredientCountConstraint
    from citrine.informatics.descriptors import FormulationDescriptor
    descriptor = FormulationDescriptor.hierarchical()
    constraint = IngredientCountConstraint(formulation_descriptor=descriptor, min=0, max=1)
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_detail=[],
        archived=True,
        display_name='formulation design space',
        id=str(uuid.uuid4()),
        config=dict(
            type='FormulationDesignSpace',
            name='formulation design space',
            description='formulates some things',
            formulation_descriptor=descriptor.dump(),
            ingredients=['foo'],
            labels={'bar': ['foo']},
            constraints=[constraint.dump()],
            resolution=0.1
        )
    )


@pytest.fixture()
def valid_gem_data_source_dict():
    return {
        "type": "hosted_table_data_source",
        "table_id": 'e5c51369-8e71-4ec6-b027-1f92bdc14762',
        "table_version": 2
    }


@pytest.fixture
def valid_auto_ml_predictor_data(valid_gem_data_source_dict):
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
    z = RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
    return dict(
        type='AutoML',
        name='AutoML predictor',
        description='Predicts z from input x',
        inputs=[x.dump()],
        outputs=[z.dump()],
        estimators=[AutoMLEstimator.RANDOM_FOREST.value],
        training_data=[]
    )


@pytest.fixture
def valid_graph_predictor_data(
        valid_simple_mixture_predictor_data,
        valid_label_fractions_predictor_data,
        valid_expression_predictor_data,
        valid_mean_property_predictor_data,
        valid_auto_ml_predictor_data
):
    """Produce valid data used for tests."""
    from citrine.informatics.data_sources import GemTableDataSource
    instance = dict(
        name='Graph predictor',
        description='description',
        predictors=[
            valid_simple_mixture_predictor_data,
            valid_label_fractions_predictor_data,
            valid_expression_predictor_data,
            valid_mean_property_predictor_data,
            valid_auto_ml_predictor_data
        ],
        training_data=[GemTableDataSource(table_id=uuid.uuid4(), table_version=0).dump()]
    )
    return PredictorEntityDataFactory(data=PredictorDataDataFactory(instance=instance))


@pytest.fixture
def valid_graph_predictor_data_empty():
    """Another predictor valid data used for tests."""
    instance = dict(
        type='Graph',
        name='Empty Graph predictor',
        description='description',
        predictors=[],
        training_data=[]
    )
    return PredictorEntityDataFactory(data=PredictorDataDataFactory(instance=instance))


@pytest.fixture
def valid_deprecated_expression_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
    return dict(
        type='Expression',
        name='Expression predictor',
        description='Computes shear modulus from Youngs modulus and Poissons ratio',
        expression='Y / (2 * (1 + v))',
        output=shear_modulus.dump(),
        aliases={
            'Y': "Property~Young's modulus",
            'v': "Property~Poisson's ratio",
        }
    )


@pytest.fixture
def valid_expression_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
    youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
    poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
    return dict(
        type='AnalyticExpression',
        name='Expression predictor',
        description='Computes shear modulus from Youngs modulus and Poissons ratio',
        expression='Y / (2 * (1 + v))',
        output=shear_modulus.dump(),
        aliases={
            'Y': youngs_modulus.dump(),
            'v': poissons_ratio.dump(),
        }
    )


@pytest.fixture
def valid_predictor_report_data(example_categorical_pva_metrics, example_f1_metrics):
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", lower_bound=0, upper_bound=1, units="")
    y = RealDescriptor("y", lower_bound=0, upper_bound=100, units="")
    z = RealDescriptor("z", lower_bound=0, upper_bound=101, units="")
    return dict(
        id='7c2dda5d-675a-41b6-829c-e485163f0e43',
        module_id='31c7f311-6f3d-4a93-9387-94cc877f170c',
        status='OK',
        create_time='2020-04-23T15:46:26Z',
        update_time='2020-04-23T15:46:26Z',
        report=dict(
            models=[
                dict(
                    name='GeneralLoloModel_1',
                    type='ML Model',
                    inputs=[x.key],
                    outputs=[y.key],
                    display_name='ML Model',
                    model_settings=[
                        dict(
                            name='Algorithm',
                            value='Ensemble of non-linear estimators',
                            children=[
                                dict(name='Number of estimators', value=64, children=[]),
                                dict(name='Leaf model', value='Mean', children=[]),
                                dict(name='Use jackknife', value=True, children=[])
                            ]
                        )
                    ],
                    feature_importances=[
                        dict(
                            response_key='y',
                            importances=dict(x=1.00),
                            top_features=5
                        )
                    ],
                    selection_summary=dict(
                        n_folds=4,
                        evaluation_results=[
                            dict(
                                model_settings=[
                                    dict(
                                        name='Algorithm',
                                        value='Ensemble of non-linear estimators',
                                        children=[
                                            dict(name='Number of estimators', value=64, children=[]),
                                            dict(name='Leaf model', value='Mean', children=[]),
                                            dict(name='Use jackknife', value=True, children=[])
                                        ]
                                    )
                                ],
                                response_results=dict(
                                    response_name=dict(
                                        metrics=dict(
                                            predicted_vs_actual=example_categorical_pva_metrics,
                                            f1=example_f1_metrics
                                        )
                                    )
                                )
                            )
                        ]
                    ),
                    predictor_configuration_name="Predict y from x with ML"
                ),
                dict(
                    name='GeneralLosslessModel_2',
                    type='Analytic Model',
                    inputs=[x.key, y.key],
                    outputs=[z.key],
                    display_name='GeneralLosslessModel_2',
                    model_settings=[
                        dict(
                            name="Expression",
                            value="(z) <- (x + y)",
                            children=[]
                        )
                    ],
                    feature_importances=[],
                    predictor_configuration_name="Expression for z",
                    predictor_configuration_uid="249bf32c-6f3d-4a93-9387-94cc877f170c"
                )
            ],
            descriptors=[x.dump(), y.dump(), z.dump()]
        )
    )


@pytest.fixture
def valid_ing_formulation_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    return dict(
        type='IngredientsToSimpleMixture',
        name='Ingredients to formulation predictor',
        description='Constructs mixtures from ingredients',
        id_to_quantity={
            'water': RealDescriptor('water quantity', lower_bound=0, upper_bound=1, units="").dump(),
            'salt': RealDescriptor('salt quantity', lower_bound=0, upper_bound=1, units="").dump()
        },
        labels={
            'solvent': ['water'],
            'solute': ['salt'],
        }
    )


@pytest.fixture
def valid_generalized_mean_property_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    formulation_descriptor = FormulationDescriptor.hierarchical()
    return dict(
        type='GeneralizedMeanProperty',
        name='Mean property predictor',
        description='Computes mean ingredient properties',
        input=formulation_descriptor.dump(),
        properties=['density'],
        p=2,
        impute_properties=True,
        default_properties={'density': 1.0},
        label='solvent'
    )


@pytest.fixture
def valid_mean_property_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    formulation_descriptor = FormulationDescriptor.flat()
    density = RealDescriptor(key='density', lower_bound=0, upper_bound=100, units='g/cm^3')
    return dict(
        type='MeanProperty',
        name='Mean property predictor',
        description='Computes mean ingredient properties',
        input=formulation_descriptor.dump(),
        properties=[density.dump()],
        p=2.0,
        impute_properties=True,
        default_properties={'density': 1.0},
        label='solvent',
        training_data=[]
    )


@pytest.fixture
def valid_label_fractions_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        type='LabelFractions',
        name='Label fractions predictor',
        description='Computes relative proportions of labeled ingredients',
        input=FormulationDescriptor.hierarchical().dump(),
        labels=['solvent']
    )


@pytest.fixture
def valid_ingredient_fractions_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        type='IngredientFractions',
        name='Ingredient fractions predictor',
        description='Computes ingredient fractions',
        input=FormulationDescriptor.hierarchical().dump(),
        ingredients=['Blue dye', 'Red dye']
    )


@pytest.fixture
def valid_data_source_design_space_dict(valid_gem_data_source_dict):
    return {
        "status": "INPROGRESS",
        "config": {
            "type": "DataSourceDesignSpace",
            "name": "Example valid data source design space",
            "description": "Example valid data source design space based on a GEM Table Data Source.",
            "data_source": valid_gem_data_source_dict
        }
    }


@pytest.fixture
def invalid_predictor_node_data():
    """Produce invalid valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
    y = RealDescriptor("y", lower_bound=0, upper_bound=100, units="")
    z = RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
    return dict(
        type='invalid',
        name='my predictor',
        description='does some things',
        inputs=[x.dump(), y.dump()],
        output=z.dump()
    )


@pytest.fixture
def invalid_graph_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
    y = RealDescriptor("y", lower_bound=0, upper_bound=100, units="")
    z = RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
    instance = dict(
        type='invalid',
        name='my predictor',
        description='does some things badly',
        predictors=[x.dump(), y.dump()],
    )
    detail = [
        StatusDetail(level=StatusLevelEnum.WARNING, msg='Something is wrong'),
        StatusDetail(level="Error", msg='Very wrong')
    ]
    status = StatusDataFactory(name='INVALID', detail=detail)
    return PredictorEntityDataFactory(
        data=PredictorDataDataFactory(instance=instance),
        meatadata=PredictorMetadataDataFactory(status=status)
    )


@pytest.fixture
def valid_simple_mixture_predictor_data():
    """Produce valid data used for tests."""
    return dict(
        type='SimpleMixture',
        name='Simple mixture predictor',
        description='simple mixture description',
        training_data=[]
    )


@pytest.fixture
def example_cv_evaluator_dict():
    return {
        "type": "CrossValidationEvaluator",
        "name": "Example evaluator",
        "description": "An evaluator for testing",
        "responses": ["salt?", "saltiness"],
        "n_folds": 6,
        "n_trials": 8,
        "metrics": [
            {"type": "PVA"}, {"type": "RMSE"}, {"type": "F1"}
        ],
        "ignore_when_grouping": ["temperature"]
    }


@pytest.fixture
def example_holdout_evaluator_dict(valid_gem_data_source_dict):
    return {
        "type": "HoldoutSetEvaluator",
        "name": "Example holdout evaluator",
        "description": "",
        "responses": ["sweetness"],
        "data_source": valid_gem_data_source_dict,
        "metrics": [{"type": "RMSE"}]
    }

@pytest.fixture()
def example_rmse_metrics():
    return {
        "type": "RealMetricValue",
        "mean": 0.4,
        "standard_error": 0.12
    }


@pytest.fixture
def example_f1_metrics():
    return {
        "type": "RealMetricValue",
        "mean": 0.3
    }


@pytest.fixture
def example_real_pva_metrics():
    return {
        "type": "RealPredictedVsActual",
        "value": [
            {
                "uuid": "0ca80829-fd17-45fb-93c9-62ea4e4c294d",
                "identifiers": ["Foo", "Bar"],
                "trial": 1,
                "fold": 3,
                "predicted": {
                    "type": "RealMetricValue",
                    "mean": 1.0,
                    "standard_error": 0.12
                },
                "actual": {
                    "type": "RealMetricValue",
                    "mean": 1.2,
                    "standard_error": 0.0
                }
            }
        ]
    }


@pytest.fixture
def example_categorical_pva_metrics():
    return {
        "type": "CategoricalPredictedVsActual",
        "value": [
            {
                "uuid": "0ca80829-fd17-45fb-93c9-62ea4e4c294d",
                "identifiers": ["Foo", "Bar"],
                "trial": 1,
                "fold": 3,
                "predicted": {
                    "salt": 0.3,
                    "not salt": 0.7
                },
                "actual": {
                    "not salt": 1.0
                }
            }
        ]
    }


@pytest.fixture()
def example_cv_result_dict(example_cv_evaluator_dict, example_rmse_metrics, example_categorical_pva_metrics, example_f1_metrics, example_real_pva_metrics):
    return {
        "type": "CrossValidationResult",
        "evaluator": example_cv_evaluator_dict,
        "response_results": {
            "salt?": {
                "metrics": {
                    "predicted_vs_actual": example_categorical_pva_metrics,
                    "f1": example_f1_metrics
                }
            },
            "saltiness": {
                "metrics": {
                    "predicted_vs_actual": example_real_pva_metrics,
                    "rmse": example_rmse_metrics
                }
            }
        }
    }


@pytest.fixture()
def example_holdout_result_dict(example_holdout_evaluator_dict, example_rmse_metrics):
    return {
        "type": "HoldoutSetResult",
        "evaluator": example_holdout_evaluator_dict,
        "response_results": {
            "sweetness": {
                "metrics": {
                    "rmse": example_rmse_metrics
                }
            }
        }
    }


@pytest.fixture
def sample_design_space_execution_dict(generic_entity):
    ret = generic_entity.copy()
    ret.update(
        {
            "design_space_id": str(uuid.uuid4()),
            "status": {
                "minor": ret.get("status_description"),
                "detail": ret.get("status_detail"),
            },
        }
    )
    return ret


@pytest.fixture()
def example_design_material():
    return {
        'vars': {
            'Temperature': {'type': 'R', 'm': 475.8, 's': 0},
            'Flour': {'type': 'C', 'cp': {'flour': 100.0}},
            'Water': {'type': 'M', 'q': {'water': 72.5}, 'l': {}},
            'Salt': {'type': 'F', 'f': 'NaCl'},
            'Yeast': {'type': 'S', 's': 'O1C=2C=C(C=3SC=C4C=CNC43)CC2C=5C=CC=6C=CNC6C15'}
        },
        'identifiers': {
            'id': str(uuid.uuid4()),
            'identifiers': [],
            'material_template': str(uuid.uuid4()),
            'process_template': str(uuid.uuid4())
        }
    }


@pytest.fixture()
def example_hierarchical_design_material(example_design_material):
    return {
        'terminal': example_design_material,
        'sub_materials': [example_design_material],
        'mixtures': {
            str(uuid.uuid4()): {'q': {'A': 0.5, 'B': 0.5}, 'l': {}}
        }
    }


@pytest.fixture()
def example_candidates(example_design_material):
    return {
        "page": 2,
        "per_page": 4,
        "response": [{
            "id": str(uuid.uuid4()),
            "material_id": str(uuid.uuid4()),
            "identifiers": [],
            "primary_score": 0,
            "material": example_design_material
        }]
    }


@pytest.fixture()
def example_sample_design_space_response(example_hierarchical_design_material):
    return {
        "per_page": 4,
        "response": [{
            "id": str(uuid.uuid4()),
            "execution_id": str(uuid.uuid4()),
            "material": example_hierarchical_design_material
        }]
    }



@pytest.fixture
def generic_entity():
    user = str(uuid.uuid4())
    return {
        "id": str(uuid.uuid4()),
        "status": "INPROGRESS",
        "status_description": "VALIDATING",
        "status_detail": [{"level": "Info", "msg": "System processing"}],
        "experimental": False,
        "experimental_reasons": [],
        "create_time": '2020-04-23T15:46:26Z',
        "update_time": '2020-04-23T15:46:26Z',
        "created_by": user,
        "updated_by": user,
    }


@pytest.fixture
def predictor_evaluation_execution_dict(generic_entity):
    ret = deepcopy(generic_entity)
    ret.update({
        "workflow_id": str(uuid.uuid4()),
        "predictor_id": str(uuid.uuid4()),
        "predictor_version": random.randint(1, 10),
        "evaluator_names": ["Example evaluator"]
    })
    return ret


@pytest.fixture
def design_execution_dict(generic_entity):
    ret = generic_entity.copy()
    ret.update({
        "workflow_id": str(uuid.uuid4()),
        "version_number": 2,
        "score": {
            "type": "MLI",
            "baselines": [],
            "constraints": [],
            "objectives": [],
            "name": "score",
            "description": ""
        },
        "descriptors": []
    })
    return ret


@pytest.fixture
def generative_design_execution_dict(generic_entity):
    ret = generic_entity.copy()
    return ret


@pytest.fixture
def example_generation_results():
    return {
        "page": 1,
        "per_page": 4,
        "response": [{
            "id": str(uuid.uuid4()),
            "execution_id": str(uuid.uuid4()),
            "result": {
                "seed": "CCCCO",
                "mutated": "CCCN",
                "fingerprint_similarity": 0.41,
                "fingerprint_type": "ECFP4",
            }
        }]
    }



@pytest.fixture
def predictor_evaluation_workflow_dict(generic_entity, example_cv_evaluator_dict, example_holdout_evaluator_dict):
    ret = deepcopy(generic_entity)
    ret.update({
        "name": "Example PEW",
        "description": "Example PEW for testing",
        "evaluators": [example_cv_evaluator_dict, example_holdout_evaluator_dict]
    })
    return ret

@pytest.fixture
def design_workflow_dict(generic_entity):
    ret = generic_entity.copy()
    ret.update({
        "name": "Example Design Workflow",
        "description": "A description! Of the Design Workflow! So you know what it's for!",
        "design_space_id": str(uuid.uuid4()),
        "predictor_id": str(uuid.uuid4()),
        "predictor_version": random.randint(1, 10),
    })
    return ret
