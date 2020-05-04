"""Tests for citrine.informatics.processors."""
import mock
import pytest
import uuid

from citrine.informatics.data_sources import AraTableDataSource
from citrine.informatics.descriptors import RealDescriptor, FormulationDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GeneralizedMeanPropertyPredictor, GraphPredictor, \
    SimpleMLPredictor, IngredientsToSimpleMixturePredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
formulation = FormulationDescriptor('formulation')
water_quantity = RealDescriptor('water quantity', 0, 1)
salt_quantity = RealDescriptor('salt quantity', 0, 1)
data_source = AraTableDataSource(uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762'), 0)


@pytest.fixture
def simple_predictor() -> SimpleMLPredictor:
    """Build a SimpleMLPredictor for testing."""
    return SimpleMLPredictor(name='ML predictor',
                             description='Predicts z from input x and latent variable y',
                             inputs=[x],
                             outputs=[z],
                             latent_variables=[y],
                             training_data=data_source)


@pytest.fixture
def graph_predictor() -> GraphPredictor:
    """Build a GraphPredictor for testing."""
    return GraphPredictor(name='Graph predictor', description='description', predictors=[uuid.uuid4(), uuid.uuid4()])


@pytest.fixture
def expression_predictor() -> ExpressionPredictor:
    """Build an ExpressionPredictor for testing."""
    return ExpressionPredictor(
        name='Expression predictor',
        description='Computes shear modulus from Youngs modulus and Poissons ratio',
        expression='Y / (2 * (1 + v))',
        output=shear_modulus,
        aliases={
            'Y': "Property~Young's modulus",
            'v': "Property~Poisson's ratio"
        })


@pytest.fixture
def ing_to_simple_mixture_predictor() -> IngredientsToSimpleMixturePredictor:
    """Build an IngredientsToSimpleMixturePredictor for testing."""
    return IngredientsToSimpleMixturePredictor(
        name='Ingredients to simple mixture predictor',
        description='Constructs a mixture from ingredient quantities',
        output=formulation,
        id_to_quantity={
            'water': water_quantity,
            'salt': salt_quantity
        },
        labels={
            'solvent': ['water'],
            'solute': ['salt']
        }
    )


@pytest.fixture
def generalized_mean_property_predictor() -> GeneralizedMeanPropertyPredictor:
    """Build a mean property predictor for testing."""
    return GeneralizedMeanPropertyPredictor(
        name='Mean property predictor',
        description='Computes mean component properties',
        input_descriptor=formulation,
        properties=['density'],
        impute_properties=True,
        training_data=data_source,
        default_properties={'density': 1.0},
        label='solvent'
    )


def test_simple_initialization(simple_predictor):
    """Make sure the correct fields go to the correct places for a simple predictor."""
    assert simple_predictor.name == 'ML predictor'
    assert simple_predictor.description == 'Predicts z from input x and latent variable y'
    assert len(simple_predictor.inputs) == 1
    assert simple_predictor.inputs[0] == x
    assert len(simple_predictor.outputs) == 1
    assert simple_predictor.outputs[0] == z
    assert len(simple_predictor.latent_variables) == 1
    assert simple_predictor.latent_variables[0] == y
    assert simple_predictor.training_data.table_id == uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')
    assert str(simple_predictor) == '<SimplePredictor \'ML predictor\'>'
    assert hasattr(simple_predictor, 'report')


def test_simple_post_build(simple_predictor):
    """Ensures we get a report from a simple predictor post_build call"""
    assert simple_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    simple_predictor.session = session
    simple_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert simple_predictor.report is not None
    assert simple_predictor.report.status == 'OK'


def test_graph_initialization(graph_predictor):
    """Make sure the correct fields go to the correct places for a graph predictor."""
    assert graph_predictor.name == 'Graph predictor'
    assert graph_predictor.description == 'description'
    assert len(graph_predictor.predictors) == 2
    assert str(graph_predictor) == '<GraphPredictor \'Graph predictor\'>'


def test_graph_post_build(graph_predictor):
    """Ensures we get a report from a graph predictor post_build call."""
    assert graph_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    graph_predictor.session = session
    graph_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert graph_predictor.report is not None
    assert graph_predictor.report.status == 'OK'


def test_expression_initialization(expression_predictor):
    """Make sure the correct fields go to the correct places for an expression predictor."""
    assert expression_predictor.name == 'Expression predictor'
    assert expression_predictor.output.key == 'Property~Shear modulus'
    assert expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert expression_predictor.aliases == {'Y': "Property~Young's modulus", 'v': "Property~Poisson's ratio"}
    assert str(expression_predictor) == '<ExpressionPredictor \'Expression predictor\'>'


def test_expression_post_build(expression_predictor):
    """Ensures we get a report from an expression predictor post_build call."""
    assert expression_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    expression_predictor.session = session
    expression_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert expression_predictor.report is not None
    assert expression_predictor.report.status == 'OK'


def test_ing_to_simple_mixture_initialization(ing_to_simple_mixture_predictor):
    """Make sure the correct fields go to the correct places for an ingredients to simple mixture predictor."""
    assert ing_to_simple_mixture_predictor.name == 'Ingredients to simple mixture predictor'
    assert ing_to_simple_mixture_predictor.output.key == 'formulation'
    assert ing_to_simple_mixture_predictor.id_to_quantity == {'water': water_quantity, 'salt': salt_quantity}
    assert ing_to_simple_mixture_predictor.labels == {'solvent': ['water'], 'solute': ['salt']}
    expected_str = '<IngredientsToSimpleMixturePredictor \'Ingredients to simple mixture predictor\'>'
    assert str(ing_to_simple_mixture_predictor) == expected_str


def test_ing_to_simple_mixture_post_build(ing_to_simple_mixture_predictor):
    """Ensures we get a report from an ingredients to simple mixture predictor post_build call."""
    assert ing_to_simple_mixture_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    ing_to_simple_mixture_predictor.session = session
    ing_to_simple_mixture_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert ing_to_simple_mixture_predictor.report is not None
    assert ing_to_simple_mixture_predictor.report.status == 'OK'


def test_generalized_mean_property_initialization(generalized_mean_property_predictor):
    """Make sure the correct fields go to the correct places for a mean property predictor."""
    assert generalized_mean_property_predictor.name == 'Mean property predictor'
    assert generalized_mean_property_predictor.input_descriptor.key == 'formulation'
    assert generalized_mean_property_predictor.properties == ['density']
    assert generalized_mean_property_predictor.impute_properties == True
    assert generalized_mean_property_predictor.training_data == data_source
    assert generalized_mean_property_predictor.default_properties == {'density': 1.0}
    assert generalized_mean_property_predictor.label == 'solvent'
    expected_str = '<GeneralizedMeanPropertyPredictor \'Mean property predictor\'>'
    assert str(generalized_mean_property_predictor) == expected_str


def test_generalized_mean_property_post_build(generalized_mean_property_predictor):
    """Ensures we get a report from a mean property predictor post_build call."""
    assert generalized_mean_property_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    generalized_mean_property_predictor.session = session
    generalized_mean_property_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert generalized_mean_property_predictor.report is not None
    assert generalized_mean_property_predictor.report.status == 'OK'
