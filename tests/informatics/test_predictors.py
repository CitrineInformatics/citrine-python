"""Tests for citrine.informatics.processors."""
import uuid
import warnings

import mock
import pytest

from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor, MolecularStructureDescriptor, \
    FormulationDescriptor, ChemicalFormulaDescriptor
from citrine.informatics.predictors import ExpressionPredictor, GraphPredictor, SimpleMLPredictor, \
    MolecularStructureFeaturizer, GeneralizedMeanPropertyPredictor, IngredientsToSimpleMixturePredictor, \
    SimpleMixturePredictor, LabelFractionsPredictor, IngredientFractionsPredictor, DeprecatedExpressionPredictor, \
    AutoMLPredictor, MeanPropertyPredictor, ChemicalFormulaFeaturizer

x = RealDescriptor("x", 0, 100, "")
y = RealDescriptor("y", 0, 100, "")
z = RealDescriptor("z", 0, 100, "")
density = RealDescriptor('density', lower_bound=0, upper_bound=100, units='g/cm^3')
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
formulation = FormulationDescriptor('formulation')
formulation_output = FormulationDescriptor('output formulation')
water_quantity = RealDescriptor('water quantity', 0, 1, "")
salt_quantity = RealDescriptor('salt quantity', 0, 1, "")
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
def chemical_featurizer() -> ChemicalFormulaFeaturizer:
    return ChemicalFormulaFeaturizer(
        name="Chemical featurizer",
        description="description",
        input_descriptor=ChemicalFormulaDescriptor("formula"),
        features=["standard"],
        excludes=None,
        powers=[1, 2]
    )


@pytest.fixture
def auto_ml() -> AutoMLPredictor:
    return AutoMLPredictor(
        name='AutoML Predictor',
        description='Predicts z from input x',
        inputs=[x],
        output=z,
        training_data=[data_source]
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
            'solvent': {'water'},
            'solute': {'salt'}
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
def mean_property_predictor() -> MeanPropertyPredictor:
    """Build a mean property predictor for testing."""
    return MeanPropertyPredictor(
        name='Mean property predictor',
        description='Computes mean ingredient properties',
        input_descriptor=formulation,
        properties=[density],
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
        labels={'solvent'}
    )


@pytest.fixture
def ingredient_fractions_predictor() -> IngredientFractionsPredictor:
    """Build a Ingredient Fractions predictor for testing."""
    return IngredientFractionsPredictor(
        name='Ingredient fractions predictor',
        description='Computes total ingredient fractions',
        input_descriptor=formulation,
        ingredients={"Green Paste", "Blue Paste"}
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


def test_simple_report(simple_predictor):
    """Ensures we get a report from a simple predictor post_build call"""
    with pytest.raises(ValueError):
        # without a project or session, this should error
        assert simple_predictor.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    simple_predictor._session = session
    simple_predictor._project_id = uuid.uuid4()
    simple_predictor.uid = uuid.uuid4()
    assert simple_predictor.report is not None
    assert session.get_resource.call_count == 1
    assert simple_predictor.report.status == 'OK'


def test_graph_initialization(graph_predictor):
    """Make sure the correct fields go to the correct places for a graph predictor."""
    assert graph_predictor.name == 'Graph predictor'
    assert graph_predictor.description == 'description'
    assert len(graph_predictor.predictors) == 2
    assert graph_predictor.training_data == [data_source]
    assert str(graph_predictor) == '<GraphPredictor \'Graph predictor\'>'



def test_deprecated_expression_initialization(deprecated_expression_predictor):
    """Make sure the correct fields go to the correct places for a deprecated expression predictor."""
    assert deprecated_expression_predictor.name == 'Expression predictor'
    assert deprecated_expression_predictor.output.key == 'Property~Shear modulus'
    assert deprecated_expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert deprecated_expression_predictor.aliases == {'Y': "Property~Young's modulus", 'v': "Property~Poisson's ratio"}
    assert str(deprecated_expression_predictor) == '<DeprecatedExpressionPredictor \'Expression predictor\'>'


def test_expression_initialization(expression_predictor):
    """Make sure the correct fields go to the correct places for an expression predictor."""
    assert expression_predictor.name == 'Expression predictor'
    assert expression_predictor.output.key == 'Property~Shear modulus'
    assert expression_predictor.expression == 'Y / (2 * (1 + v))'
    assert expression_predictor.aliases == {'Y': youngs_modulus, 'v': poissons_ratio}
    assert str(expression_predictor) == '<ExpressionPredictor \'Expression predictor\'>'


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


def test_chemical_featurizer(chemical_featurizer):
    assert chemical_featurizer.name == "Chemical featurizer"
    assert chemical_featurizer.description == "description"
    assert chemical_featurizer.input_descriptor == ChemicalFormulaDescriptor("formula")
    assert chemical_featurizer.features == ["standard"]
    assert chemical_featurizer.excludes == []
    assert chemical_featurizer.powers == [1, 2]

    assert str(chemical_featurizer) == "<ChemicalFormulaFeaturizer 'Chemical featurizer'>"

    assert chemical_featurizer.dump() == {
        'config': {
            'name': 'Chemical featurizer',
            'description': 'description',
            'input': ChemicalFormulaDescriptor("formula").dump(),
            'features': ['standard'],
            'excludes': [],
            'powers': [1, 2],
            'type': 'ChemicalFormulaFeaturizer'
        },
        'archived': False,
        'module_type': 'PREDICTOR',
        'display_name': 'Chemical featurizer'
    }


def test_auto_ml(auto_ml):
    assert auto_ml.name == "AutoML Predictor"
    assert auto_ml.description == "Predicts z from input x"
    assert auto_ml.inputs == [x]
    assert auto_ml.output == z
    assert auto_ml.training_data == [data_source]
    assert auto_ml.dump()['config']['outputs'] == [z.dump()]

    assert str(auto_ml) == "<AutoMLPredictor 'AutoML Predictor'>"


def test_ing_to_simple_mixture_initialization(ing_to_simple_mixture_predictor):
    """Make sure the correct fields go to the correct places for an ingredients to simple mixture predictor."""
    assert ing_to_simple_mixture_predictor.name == 'Ingredients to simple mixture predictor'
    assert ing_to_simple_mixture_predictor.output.key == 'formulation'
    assert ing_to_simple_mixture_predictor.id_to_quantity == {'water': water_quantity, 'salt': salt_quantity}
    assert ing_to_simple_mixture_predictor.labels == {'solvent': {'water'}, 'solute': {'salt'}}
    expected_str = '<IngredientsToSimpleMixturePredictor \'Ingredients to simple mixture predictor\'>'
    assert str(ing_to_simple_mixture_predictor) == expected_str


def test_deprecated_ing_to_simple_mixture():
    """Make sure a warning is issued for deprecated labels format"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ing_to_simple_mixture_predictor = IngredientsToSimpleMixturePredictor(
            name='deprecated',
            description='labels as List[str]',
            output=FormulationDescriptor('formulation'),
            id_to_quantity={'ingredient': RealDescriptor('ingredient quantity', 0, 1, '')},
            labels={'label': ['ingredient']}
        )
        assert ing_to_simple_mixture_predictor.labels == {'label': {'ingredient'}}
        assert len(w) == 1
        recorded_warning = w[0]
        assert issubclass(recorded_warning.category, DeprecationWarning)
        assert str(recorded_warning.message).startswith(
            'Labels for predictor'
        )

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


def test_mean_property_initialization(mean_property_predictor):
    """Make sure the correct fields go to the correct places for a mean property predictor."""
    assert mean_property_predictor.name == 'Mean property predictor'
    assert mean_property_predictor.input_descriptor.key == 'formulation'
    assert mean_property_predictor.properties == [density]
    assert mean_property_predictor.p == 2
    assert mean_property_predictor.impute_properties == True
    assert mean_property_predictor.training_data == [formulation_data_source]
    assert mean_property_predictor.default_properties == {'density': 1.0}
    assert mean_property_predictor.label == 'solvent'
    expected_str = '<MeanPropertyPredictor \'Mean property predictor\'>'
    assert str(mean_property_predictor) == expected_str


def test_deprecated_gmpp():
    """Make sure deprecation warnings are issued"""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        gmpp = GeneralizedMeanPropertyPredictor(
            name='deprecated',
            description='p as float',
            input_descriptor=FormulationDescriptor('formulation'),
            properties=['foo'],
            p=2.0,
            impute_properties=False
        )
        assert gmpp.p == 2
        assert len(caught) == 2
        for w in caught:
            assert issubclass(w.category, DeprecationWarning)
            msg = str(w.message)
            assert msg.startswith('p must be an integer') or \
                   msg.startswith('GeneralizedMeanPropertyPredictor is deprecated')


def test_label_fractions_property_initialization(label_fractions_predictor):
    """Make sure the correct fields go to the correct places for a label fraction predictor."""
    assert label_fractions_predictor.name == 'Label fractions predictor'
    assert label_fractions_predictor.input_descriptor.key == 'formulation'
    assert label_fractions_predictor.labels == {'solvent'}
    expected_str = '<LabelFractionsPredictor \'Label fractions predictor\'>'
    assert str(label_fractions_predictor) == expected_str


def test_deprecated_label_fractions():
    """Make sure a warning is issued for deprecated labels format"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        label_fractions_predictor = LabelFractionsPredictor(
            name='deprecated',
            description='labels as List[str]',
            input_descriptor=FormulationDescriptor('formulation'),
            labels=['label']
        )
        assert label_fractions_predictor.labels == {'label'}
        assert len(w) == 1
        recorded_warning = w[0]
        assert issubclass(recorded_warning.category, DeprecationWarning)
        assert str(recorded_warning.message).startswith(
            'Labels for predictor'
        )

def test_simple_mixture_predictor_initialization(simple_mixture_predictor):
    """Make sure the correct fields go to the correct places for a simple mixture predictor."""
    assert simple_mixture_predictor.name == 'Simple mixture predictor'
    assert simple_mixture_predictor.input_descriptor.key == 'formulation'
    assert simple_mixture_predictor.output_descriptor.key == 'output formulation'
    assert simple_mixture_predictor.training_data == [formulation_data_source]
    expected_str = '<SimpleMixturePredictor \'Simple mixture predictor\'>'
    assert str(simple_mixture_predictor) == expected_str


def test_ingredient_fractions_property_initialization(ingredient_fractions_predictor):
    """Make sure the correct fields go to the correct places for an ingredient fractions predictor."""
    assert ingredient_fractions_predictor.name == 'Ingredient fractions predictor'
    assert ingredient_fractions_predictor.input_descriptor.key == 'formulation'
    assert ingredient_fractions_predictor.ingredients == {"Green Paste", "Blue Paste"}
    expected_str = '<IngredientFractionsPredictor \'Ingredient fractions predictor\'>'
    assert str(ingredient_fractions_predictor) == expected_str


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
