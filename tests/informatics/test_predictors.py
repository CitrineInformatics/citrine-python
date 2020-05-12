"""Tests for citrine.informatics.processors."""
import mock
import pytest
import uuid

from citrine.informatics.data_sources import AraTableDataSource
from citrine.informatics.descriptors import RealDescriptor, MolecularStructureDescriptor, FormulationDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GraphPredictor, SimpleMLPredictor, \
    MolecularStructureFeaturizer, GeneralizedMeanPropertyPredictor, IngredientsToSimpleMixturePredictor, \
    LabelFractionsPredictor

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
def molecule_featurizer() -> MolecularStructureFeaturizer:
    return MolecularStructureFeaturizer(
        name="Molecule featurizer",
        description="description",
        descriptor=MolecularStructureDescriptor("SMILES"),
        features=["all"],
        excludes=["standard"]
    )


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
        description='Computes mean ingredient properties',
        input_descriptor=formulation,
        properties=['density'],
        p=2,
        training_data=data_source,
        impute_properties=True,
        default_properties={'density': 1.0},
        label='solvent'
    )


@pytest.fixture
def label_fractions_predictor() -> LabelFractionsPredictor:
    """Build a label fractions predictor for testing"""
    return LabelFractionsPredictor(
        name='Label fractions predictor',
        description='Compute relative proportions of labeled ingredients',
        input_descriptor=formulation,
        labels=['solvent']
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
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
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
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=str(uuid.uuid4()))
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
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    expression_predictor.session = session
    expression_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert expression_predictor.report is not None
    assert expression_predictor.report.status == 'OK'


def test_molecule_featurizer(molecule_featurizer):
    assert molecule_featurizer.name == "Molecule featurizer"
    assert molecule_featurizer.description == "description"
    assert molecule_featurizer.descriptor == MolecularStructureDescriptor("SMILES")
    assert molecule_featurizer.features == ["all"]
    assert molecule_featurizer.excludes == ["standard"]

    assert str(molecule_featurizer) == "<MolecularStructureFeaturizer 'Molecule featurizer'>"

    assert molecule_featurizer.dump() == {
        'config': {
            'name': 'Molecule featurizer', 'description': 'description',
            'descriptor': {'descriptor_key': 'SMILES', 'type': 'Organic'},
            'features': ['all'], 'excludes': ['standard'],
            'type': 'MoleculeFeaturizer'
        },
        'active': True,
        'module_type': 'PREDICTOR',
        'schema_id': '24183b2f-848c-46fa-8640-21b7743e38a3',
        'display_name': 'Molecule featurizer'
    }


def test_molecule_featurizer_post_build(molecule_featurizer):
    """Ensures we get a report from a molecule featurizer post_build call."""
    predictor = molecule_featurizer

    assert predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    predictor.session = session
    predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert predictor.report is not None
    assert predictor.report.status == 'OK'


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
    assert generalized_mean_property_predictor.p == 2
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


def test_label_fractions_property_initialization(label_fractions_predictor):
    """Make sure the correct fields go to the correct places for a label fraction predictor."""
    assert label_fractions_predictor.name == 'Label fractions predictor'
    assert label_fractions_predictor.input_descriptor.key == 'formulation'
    assert label_fractions_predictor.labels == ['solvent']
    expected_str = '<LabelFractionsPredictor \'Label fractions predictor\'>'
    assert str(label_fractions_predictor) == expected_str


def test_label_fractions_property_post_build(label_fractions_predictor):
    """Ensures we get a report from a label fraction predictor post_build call."""
    assert label_fractions_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    label_fractions_predictor.session = session
    label_fractions_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert label_fractions_predictor.report is not None
    assert label_fractions_predictor.report.status == 'OK'
