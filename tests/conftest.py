import uuid
from copy import deepcopy

import pytest


@pytest.fixture
def valid_product_design_space_data():
    """Produce valid product design space data."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        archived=False,
        display_name='my design space',
        schema_id='6c16d694-d015-42a7-b462-8ef299473c9a',
        id=str(uuid.uuid4()),
        config=dict(
            type='ProductDesignSpace',
            name='my design space',
            description='does some things',
            subspaces=[
                dict(
                    module_type='DESIGN_SPACE',
                    status='READY',
                    id=str(uuid.uuid4()),
                    archived=False,
                    name='first subspace',
                    instance=dict(
                        type='FormulationDesignSpace',
                        name='first subspace',
                        description='',
                        formulation_descriptor=FormulationDescriptor('X').dump(),
                        ingredients=['foo'],
                        labels={'bar': ['foo']},
                        constraints=[],
                        resolution=0.1
                    )
                ),
                dict(
                    module_type='DESIGN_SPACE',
                    status='CREATED',
                    id=None,
                    archived=False,
                    name='second subspace',
                    instance=dict(
                        type='FormulationDesignSpace',
                        name='second subspace',
                        description='formulates some things',
                        formulation_descriptor=FormulationDescriptor('Y').dump(),
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
                    template_id=str(uuid.uuid4()),
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
                    template_id=str(uuid.uuid4()),
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
        status_info=None,
        archived=True,
        display_name='my enumerated design space',
        schema_id='f3907a58-aa46-462c-8837-a5aa9605e79e',
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
                    descriptor_key='formula',
                    threshold=1.0
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
    descriptor = FormulationDescriptor('formulation')
    constraint = IngredientCountConstraint(formulation_descriptor=descriptor, min=0, max=1)
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        archived=True,
        display_name='formulation design space',
        schema_id='f3907a58-aa46-462c-8837-a5aa9605e79e',
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
        "table_version": 2,
        "formulation_descriptor": None
    }


@pytest.fixture
def valid_simple_ml_predictor_data(valid_gem_data_source_dict):
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", 0, 100, "")
    y = RealDescriptor("y", 0, 100, "")
    z = RealDescriptor("z", 0, 100, "")
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='ML predictor',
        schema_id='08d20e5f-e329-4de0-a90a-4b5e36b91703',
        id=str(uuid.uuid4()),
        config=dict(
            type='Simple',
            name='ML predictor',
            description='Predicts z from input x and latent variable y',
            inputs=[x.dump()],
            outputs=[z.dump()],
            latent_variables=[y.dump()],
            training_data=[valid_gem_data_source_dict]
        )
    )


@pytest.fixture
def valid_graph_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.descriptors import RealDescriptor
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Graph predictor',
        schema_id='43c61ad4-7e33-45d0-a3de-504acb4e0737',
        id=str(uuid.uuid4()),
        config=dict(
            type='Graph',
            name='Graph predictor',
            description='description',
            predictors=[
                str(uuid.uuid4()),
                dict(
                    type='Expression',
                    name='Expression predictor',
                    description='mean of 2 outputs',
                    expression='(X + Y)/2',
                    output=RealDescriptor(
                        'Property~Some metric', lower_bound=0, upper_bound=1000, units='W'
                    ).dump(),
                    aliases={
                        "Property~X": "X",
                        "Property~Y": "Y"
                    }
                )
            ],
            training_data=[GemTableDataSource(uuid.uuid4(), 0).dump()]
        )
    )


@pytest.fixture
def valid_deprecated_expression_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Expression predictor',
        schema_id='866e72a6-0a01-4c5f-8c35-146eb2540166',
        id=str(uuid.uuid4()),
        config=dict(
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
    )


@pytest.fixture
def valid_expression_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
    youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
    poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Expression predictor',
        schema_id='f1601161-bb98-4fa9-bdd2-a2a673547532',
        id=str(uuid.uuid4()),
        config=dict(
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
    )


@pytest.fixture
def valid_predictor_report_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", 0, 1, "")
    y = RealDescriptor("y", 0, 100, "")
    z = RealDescriptor("z", 0, 101, "")
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
def valid_ing_to_simple_mixture_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Ingredients to simple mixture predictor',
        schema_id='873e4541-da8a-4698-a981-732c0c729c3d',
        id=str(uuid.uuid4()),
        config=dict(
            type='IngredientsToSimpleMixture',
            name='Ingredients to simple mixture predictor',
            description='Constructs mixtures from ingredients',
            output=FormulationDescriptor('simple mixture').dump(),
            id_to_quantity={
                'water': RealDescriptor('water quantity', 0, 1).dump(),
                'salt': RealDescriptor('salt quantity', 0, 1).dump()
            },
            labels={
                'solvent': ['water'],
                'solute': ['salt'],
            }
        )
    )


@pytest.fixture
def valid_generalized_mean_property_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    from citrine.informatics.data_sources import GemTableDataSource
    formulation_descriptor = FormulationDescriptor('simple mixture')
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Mean property predictor',
        schema_id='29e53222-3217-4f81-b3b8-4197a8211ade',
        id=str(uuid.uuid4()),
        config=dict(
            type='GeneralizedMeanProperty',
            name='Mean property predictor',
            description='Computes mean ingredient properties',
            input=formulation_descriptor.dump(),
            properties=['density'],
            p=2,
            training_data=[GemTableDataSource(uuid.uuid4(), 0, formulation_descriptor).dump()],
            impute_properties=True,
            default_properties={'density': 1.0},
            label='solvent'
        )
    )


@pytest.fixture
def valid_label_fractions_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Label fractions predictor',
        schema_id='997a7e11-2c16-4e30-b531-9e657a863019',
        id=str(uuid.uuid4()),
        config=dict(
            type='LabelFractions',
            name='Label fractions predictor',
            description='Computes relative proportions of labeled ingredients',
            input=FormulationDescriptor('simple mixture').dump(),
            labels=['solvent']
        )
    )


@pytest.fixture
def valid_ingredient_fractions_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import FormulationDescriptor
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Ingredient fractions predictor',
        schema_id='eb02a095-8cdc-45d8-bc82-1013b6e8e700',
        id=str(uuid.uuid4()),
        config=dict(
            type='IngredientFractions',
            name='Ingredient fractions predictor',
            description='Computes ingredient fractions',
            input=FormulationDescriptor('ingredients').dump(),
            ingredients=['Blue dye', 'Red dye']
        )
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
def invalid_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", 0, 100, "")
    y = RealDescriptor("y", 0, 100, "")
    z = RealDescriptor("z", 0, 100, "")
    return dict(
        module_type='PREDICTOR',
        status='INVALID',
        status_info=['Something is wrong', 'Very wrong'],
        archived=True,
        display_name='my predictor',
        schema_id='ff26b280-8a8b-46ab-b7aa-0c73ff84b0fd',
        id=str(uuid.uuid4()),
        config=dict(
            type='invalid',
            name='my predictor',
            description='does some things',
            inputs=[x.dump(), y.dump()],
            output=z.dump()
        )
    )


@pytest.fixture
def valid_grid_processor_data():
    """Valid GridProcessor data."""
    return dict(
        module_type='PROCESSOR',
        status='READY',
        status_info=['Things are looking good'],
        archived=False,
        display_name='my processor',
        schema_id='272791a5-5468-4344-ac9f-2811d9266a4d',
        id=str(uuid.uuid4()),
        config=dict(
            type='Grid',
            name='my processor',
            description='does some things',
            grid_dimensions=dict(x=5, y=10),
        )
    )


@pytest.fixture
def valid_simple_mixture_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.descriptors import FormulationDescriptor
    input_formulation = FormulationDescriptor('input formulation')
    output_formulation = FormulationDescriptor('output formulation')
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        archived=False,
        display_name='Simple mixture predictor',
        schema_id='e82a993c-e6ab-46a2-b636-c71d0ba224d1',
        id=str(uuid.uuid4()),
        config=dict(
            type='SimpleMixture',
            name='Simple mixture predictor',
            description='simple mixture description',
            input=input_formulation.dump(),
            output=output_formulation.dump(),
            training_data=[GemTableDataSource(uuid.uuid4(), 0, input_formulation).dump()]
        ),
    )


@pytest.fixture()
def example_evaluator_dict():
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
def example_result_dict(example_evaluator_dict, example_rmse_metrics, example_categorical_pva_metrics, example_f1_metrics, example_real_pva_metrics):
    return {
        "type": "CrossValidationResult",
        "evaluator": example_evaluator_dict,
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


@pytest.fixture
def generic_entity():
    user = str(uuid.uuid4())
    return {
        "id": str(uuid.uuid4()),
        "status": "INPROGRESS",
        "status_description": "VALIDATING",
        "status_info": ["System processing"],
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
        "evaluator_names": ["Example evaluator"]
    })
    return ret


@pytest.fixture
def predictor_evaluation_workflow_dict(generic_entity, example_evaluator_dict):
    ret = deepcopy(generic_entity)
    ret.update({
        "name": "Example PEW",
        "description": "Example PEW for testing",
        "evaluators": [example_evaluator_dict]
    })
    return ret
