import uuid
import pytest


@pytest.fixture
def valid_product_design_space_data():
    """Produce valid product design space data."""
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        active=True,
        display_name='my design space',
        schema_id='6c16d694-d015-42a7-b462-8ef299473c9a',
        id=str(uuid.uuid4()),
        config=dict(
            type='Univariate',
            name='my design space',
            description='does some things',
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
                        descriptor_values=['red', 'green', 'blue'],
                    ),
                    list=['red']
                )
            ]
        )
    )

@pytest.fixture
def valid_enumerated_design_space_data():
    """Produce valid enumerated design space data."""
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        active=False,
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
                    descriptor_values=['red', 'green', 'blue'],
                )
            ],
            data=[
                dict(x=1, color='red'),
                dict(x=2.0, color='green')
            ]
        )
    )


@pytest.fixture
def valid_simple_ml_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    x = RealDescriptor("x", 0, 100, "")
    y = RealDescriptor("y", 0, 100, "")
    z = RealDescriptor("z", 0, 100, "")
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        active=True,
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
            training_data=dict(
                table_id='e5c51369-8e71-4ec6-b027-1f92bdc14762',
                table_version='latest'
            )
        )
    )


@pytest.fixture
def valid_graph_predictor_data(valid_expression_predictor_data):
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        active=True,
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
                    module_type='PREDICTOR',
                    active=True,
                    display_name='Expression predictor',
                    schema_id='866e72a6-0a01-4c5f-8c35-146eb2540166',
                    config=dict(
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
                )
            ]
        )
    )


@pytest.fixture
def valid_expression_predictor_data():
    """Produce valid data used for tests."""
    from citrine.informatics.descriptors import RealDescriptor
    shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
    return dict(
        module_type='PREDICTOR',
        status='VALID',
        status_info=[],
        active=True,
        display_name='Expression predictor',
        schema_id='e7d79c73-8bf3-4609-887a-7f31b9cef566',
        id=str(uuid.uuid4()),
        config=dict(
            type='Expression',
            name='Expression predictor',
            description='Computes shear modulus from Youngs modulus and Poissons ratio',
            expression='Y / (2 * (1 + v))',
            output=shear_modulus.dump(),
            aliases={
                "Property~Young's modulus": 'Y',
                "Property~Poisson's ratio": 'v',
            }
        )
    )


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
        active=False,
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
        active=True,
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
def valid_enumerated_processor_data():
    """Valid EnumeratedProcessor data."""
    return dict(
        module_type='PROCESSOR',
        status='READY',
        status_info=['valid'],
        active=True,
        display_name='my enumerated processor',
        schema_id='272791a5-5468-4344-ac9f-2811d9266a4d',
        id=str(uuid.uuid4()),
        config=dict(
            type='Enumerated',
            name='my enumerated processor',
            description='enumerates all the things',
            max_size=10,
        )
    )
