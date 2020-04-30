"""Tests for citrine.informatics.processors."""
import mock
import pytest
import uuid

from citrine.informatics.data_sources import AraTableDataSource
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GraphPredictor, SimpleMLPredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')


@pytest.fixture
def simple_predictor() -> SimpleMLPredictor:
    """Build a SimpleMLPredictor for testing."""
    return SimpleMLPredictor(name='ML predictor',
                             description='Predicts z from input x and latent variable y',
                             inputs=[x],
                             outputs=[z],
                             latent_variables=[y],
                             training_data=AraTableDataSource(uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762'), 0))


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
        aliases = {
             'Y': "Property~Young's modulus",
             'v': "Property~Poisson's ratio"
        })


def test_simple_initialization(simple_predictor):
    """Make sure the correct fields go to the correct places for the Simple Predictor."""
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
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    simple_predictor.session = session
    simple_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert simple_predictor.report is not None
    assert simple_predictor.report.status == 'OK'


def test_graph_initialization(graph_predictor):
    """Make sure the correct fields go to the correct places for the Graph Predictor."""
    assert graph_predictor.name == 'Graph predictor'
    assert graph_predictor.description == 'description'
    assert len(graph_predictor.predictors) == 2
    assert str(graph_predictor) == '<GraphPredictor \'Graph predictor\'>'


def test_graph_post_build(graph_predictor):
    """Ensures we get a report from a graph predictor post_build call."""
    assert graph_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=str(uuid.uuid4()))
    graph_predictor.session = session
    graph_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert graph_predictor.report is not None
    assert graph_predictor.report.status == 'OK'


def test_expression_initialization(expression_predictor):
    """Make sure the correct fields go to the correct places for the Expression Predictor."""
    assert expression_predictor.name == 'Expression predictor'
    assert expression_predictor.output.key == 'Property~Shear modulus'
    assert expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert expression_predictor.aliases == {'Y': "Property~Young's modulus", 'v': "Property~Poisson's ratio"}
    assert str(expression_predictor) == '<ExpressionPredictor \'Expression predictor\'>'


def test_expression_post_build(expression_predictor):
    """Ensures we get a report from a expression predictor post_build call."""
    assert expression_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    expression_predictor.session = session
    expression_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert expression_predictor.report is not None
    assert expression_predictor.report.status == 'OK'
