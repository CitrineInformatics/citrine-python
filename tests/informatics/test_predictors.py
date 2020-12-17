"""Tests for citrine.informatics.processors."""
import uuid
import warnings

import mock
import pytest

from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor, MolecularStructureDescriptor, FormulationDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GraphPredictor, SimpleMLPredictor, \
    MolecularStructureFeaturizer, GeneralizedMeanPropertyPredictor, IngredientsToSimpleMixturePredictor, \
    SimpleMixturePredictor, LabelFractionsPredictor, IngredientFractionsPredictor, DeprecatedExpressionPredictor

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
formulation = FormulationDescriptor('formulation')
formulation_output = FormulationDescriptor('output formulation')
water_quantity = RealDescriptor('water quantity', 0, 1)
salt_quantity = RealDescriptor('salt quantity', 0, 1)
data_source = GemTableDataSource(uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762'), 0)
formulation_data_source = GemTableDataSource(uuid.UUID('6894a181-81d2-4304-9dfa-a6c5b114d8bc'), 0, formulation)


@pytest.fixture
def simple_predictor() -> SimpleMLPredictor:
    """Build a SimpleMLPredictor for testing."""
    return SimpleMLPredictor(name='ML predictor',
                             description='Predicts z from input x and latent variable y',
                             inputs=[x],
                             outputs=[z],
                             latent_variables=[y],
                             training_data=[data_source])


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
    return GraphPredictor(
        name='Graph predictor',
        description='description',
        predictors=[uuid.uuid4(), uuid.uuid4()],
        training_data=[data_source]
    )


@pytest.fixture
def deprecated_expression_predictor() -> DeprecatedExpressionPredictor:
    """Build a DeprecatedExpressionPredictor for testing."""
    return DeprecatedExpressionPredictor(
        name='Expression predictor',
        description='Computes shear modulus from Youngs modulus and Poissons ratio',
        expression='Y / (2 * (1 + v))',
        output=shear_modulus,
        aliases={
            'Y': "Property~Young's modulus",
            'v': "Property~Poisson's ratio"
        })


@pytest.fixture
def expression_predictor() -> ExpressionPredictor:
    """Build an ExpressionPredictor for testing."""
    return ExpressionPredictor(
        name='Expression predictor',
        description='Computes shear modulus from Youngs modulus and Poissons ratio',
        expression='Y / (2 * (1 + v))',
        output=shear_modulus,
        aliases={
            'Y': youngs_modulus,
            'v': poissons_ratio
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
        training_data=[formulation_data_source],
        impute_properties=True,
        default_properties={'density': 1.0},
        label='solvent'
    )


@pytest.fixture
def simple_mixture_predictor() -> SimpleMixturePredictor:
    """Build a simple mixture predictor for testing."""
    return SimpleMixturePredictor(
        name='Simple mixture predictor',
        description='Computes mean ingredient properties',
        input_descriptor=formulation,
        output_descriptor=formulation_output,
        training_data=[formulation_data_source]
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


@pytest.fixture
def ingredient_fractions_predictor() -> IngredientFractionsPredictor:
    """Build a Ingredient Fractions predictor for testing."""
    return IngredientFractionsPredictor(
        name='Ingredient fractions predictor',
        description='Computes total ingredient fractions',
        input_descriptor=formulation,
        ingredients=["Green Paste", "Blue Paste"]
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
    assert simple_predictor.training_data[0].table_id == uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762')
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
    assert graph_predictor.training_data == [data_source]
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


def test_deprecated_expression_initialization(deprecated_expression_predictor):
    """Make sure the correct fields go to the correct places for a deprecated expression predictor."""
    assert deprecated_expression_predictor.name == 'Expression predictor'
    assert deprecated_expression_predictor.output.key == 'Property~Shear modulus'
    assert deprecated_expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert deprecated_expression_predictor.aliases == {'Y': "Property~Young's modulus", 'v': "Property~Poisson's ratio"}
    assert str(deprecated_expression_predictor) == '<DeprecatedExpressionPredictor \'Expression predictor\'>'


def test_deprecated_expression_post_build(deprecated_expression_predictor):
    """Ensures we get a report from a deprecated expression predictor post_build call."""
    assert deprecated_expression_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    deprecated_expression_predictor.session = session
    deprecated_expression_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert deprecated_expression_predictor.report is not None
    assert deprecated_expression_predictor.report.status == 'OK'


def test_expression_initialization(expression_predictor):
    """Make sure the correct fields go to the correct places for an expression predictor."""
    assert expression_predictor.name == 'Expression predictor'
    assert expression_predictor.output.key == 'Property~Shear modulus'
    assert expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert expression_predictor.aliases == {'Y': youngs_modulus, 'v': poissons_ratio}
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
        'archived': False,
        'module_type': 'PREDICTOR',
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
    assert generalized_mean_property_predictor.training_data == [formulation_data_source]
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


def test_simple_mixture_predictor_initialization(simple_mixture_predictor):
    """Make sure the correct fields go to the correct places for a simple mixture predictor."""
    assert simple_mixture_predictor.name == 'Simple mixture predictor'
    assert simple_mixture_predictor.input_descriptor.key == 'formulation'
    assert simple_mixture_predictor.output_descriptor.key == 'output formulation'
    assert simple_mixture_predictor.training_data == [formulation_data_source]
    expected_str = '<SimpleMixturePredictor \'Simple mixture predictor\'>'
    assert str(simple_mixture_predictor) == expected_str


def test_simple_mixture_relation_post_build(simple_mixture_predictor):
    """Ensures we get a report from a simple mixture predictor post_build call."""
    assert simple_mixture_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    simple_mixture_predictor.session = session
    simple_mixture_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert simple_mixture_predictor.report is not None
    assert simple_mixture_predictor.report.status == 'OK'


def test_ingredient_fractions_property_initialization(ingredient_fractions_predictor):
    """Make sure the correct fields go to the correct places for an ingredient fractions predictor."""
    assert ingredient_fractions_predictor.name == 'Ingredient fractions predictor'
    assert ingredient_fractions_predictor.input_descriptor.key == 'formulation'
    assert ingredient_fractions_predictor.ingredients == ["Green Paste", "Blue Paste"]
    expected_str = '<IngredientFractionsPredictor \'Ingredient fractions predictor\'>'
    assert str(ingredient_fractions_predictor) == expected_str


def test_ingredient_fractions_property_post_build(ingredient_fractions_predictor):
    """Ensures we get a report from a ingredient fraction predictor post_build call."""
    assert ingredient_fractions_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(), uid=uuid.uuid4())
    ingredient_fractions_predictor.session = session
    ingredient_fractions_predictor.post_build(uuid.uuid4(), dict(id=uuid.uuid4()))
    assert session.get_resource.call_count == 1
    assert ingredient_fractions_predictor.report is not None
    assert ingredient_fractions_predictor.report.status == 'OK'


def test_wrap_training_data():
    """Test training data is converted to a list if ``None`` or a single source."""
    predictor_without_data = GraphPredictor(
        name="",
        description="",
        predictors=[],
        training_data=None
    )
    assert predictor_without_data.training_data == []

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        predictor_single_data_source = GraphPredictor(
            name="",
            description="",
            predictors=[],
            training_data=data_source
        )
        assert predictor_single_data_source.training_data == [data_source]
        assert len(w) == 1
        recorded_warning = w[0]
        assert issubclass(recorded_warning.category, DeprecationWarning)
        assert str(recorded_warning.message).startswith(
            "Specifying training data as a single data source is deprecated."
        )

    predictor_multiple_data_sources = GraphPredictor(
        name="",
        description="",
        predictors=[],
        training_data=[data_source, formulation_data_source]
    )
    assert predictor_multiple_data_sources.training_data == [data_source, formulation_data_source]
