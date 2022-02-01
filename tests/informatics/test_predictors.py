"""Tests for citrine.informatics.predictors."""
import uuid
import mock
import pytest

from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor, MolecularStructureDescriptor, \
    FormulationDescriptor, ChemicalFormulaDescriptor, CategoricalDescriptor
from citrine.informatics.predictors import *

x = RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
y = RealDescriptor("y", lower_bound=0, upper_bound=100, units="")
z = RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
density = RealDescriptor('density', lower_bound=0, upper_bound=100, units='g/cm^3')
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
chain_type = CategoricalDescriptor('Chain Type', categories={'Gaussian Coil', 'Rigid Rod', 'Worm-like'})
formulation = FormulationDescriptor('formulation')
formulation_output = FormulationDescriptor('output formulation')
water_quantity = RealDescriptor('water quantity', lower_bound=0, upper_bound=1, units="")
salt_quantity = RealDescriptor('salt quantity', lower_bound=0, upper_bound=1, units="")
data_source = GemTableDataSource(table_id=uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762'), table_version=0)
formulation_data_source = GemTableDataSource(table_id=uuid.UUID('6894a181-81d2-4304-9dfa-a6c5b114d8bc'), table_version=0, formulation_descriptor=formulation)


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
        input_descriptor=MolecularStructureDescriptor("SMILES"),
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
def ing_to_formulation_predictor() -> IngredientsToFormulationPredictor:
    """Build an IngredientsToFormulationPredictor for testing."""
    return IngredientsToFormulationPredictor(
        name='Ingredients to formulation predictor',
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
def mean_property_predictor() -> MeanPropertyPredictor:
    """Build a mean property predictor for testing."""
    return MeanPropertyPredictor(
        name='Mean property predictor',
        description='Computes mean ingredient properties',
        input_descriptor=formulation,
        properties=[density, chain_type],
        p=2.5,
        training_data=[formulation_data_source],
        impute_properties=True,
        default_properties={'density': 1.0, 'Chain Type': 'Gaussian Coil'},
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
    assert molecule_featurizer.input_descriptor == MolecularStructureDescriptor("SMILES")
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


def test_ing_to_formulation_initialization(ing_to_formulation_predictor):
    """Make sure the correct fields go to the correct places for an ingredients to formulation predictor."""
    assert ing_to_formulation_predictor.name == 'Ingredients to formulation predictor'
    assert ing_to_formulation_predictor.output.key == 'formulation'
    assert ing_to_formulation_predictor.id_to_quantity == {'water': water_quantity, 'salt': salt_quantity}
    assert ing_to_formulation_predictor.labels == {'solvent': {'water'}, 'solute': {'salt'}}
    expected_str = f'<IngredientsToFormulationPredictor \'{ing_to_formulation_predictor.name}\'>'
    assert str(ing_to_formulation_predictor) == expected_str


def test_mean_property_initialization(mean_property_predictor):
    """Make sure the correct fields go to the correct places for a mean property predictor."""
    assert mean_property_predictor.name == 'Mean property predictor'
    assert mean_property_predictor.input_descriptor.key == 'formulation'
    assert mean_property_predictor.properties == [density, chain_type]
    assert mean_property_predictor.p == 2.5
    assert mean_property_predictor.impute_properties == True
    assert mean_property_predictor.training_data == [formulation_data_source]
    assert mean_property_predictor.default_properties == {'density': 1.0, 'Chain Type': 'Gaussian Coil'}
    assert mean_property_predictor.label == 'solvent'
    expected_str = '<MeanPropertyPredictor \'Mean property predictor\'>'
    assert str(mean_property_predictor) == expected_str


def test_mean_property_round_robin(mean_property_predictor):
    """Make sure that the MPP can be de/serialized appropriately."""
    data = mean_property_predictor.dump()
    new_mpp = MeanPropertyPredictor.build(data)
    real_props = [d for d in new_mpp.properties if isinstance(d, RealDescriptor)]
    cat_props = [d for d in new_mpp.properties if isinstance(d, CategoricalDescriptor)]
    assert len(new_mpp.properties) == 2
    assert len(real_props) == 1
    assert len(cat_props) == 1


def test_deprecated_ingredients_to_simple_mixture():
    """make sure deprecation warnings are issued."""
    with pytest.warns(DeprecationWarning):
        i2sm = IngredientsToSimpleMixturePredictor(
            name="deprecated",
            description="",
            output=FormulationDescriptor("formulation"),
            id_to_quantity={"quantity 1": RealDescriptor("foo", lower_bound=0, upper_bound=1, units="")},
            labels={"label": {"foo"}}
        )
        assert i2sm.name == "deprecated"
        assert i2sm.labels == {"label": {"foo"}}


def test_label_fractions_property_initialization(label_fractions_predictor):
    """Make sure the correct fields go to the correct places for a label fraction predictor."""
    assert label_fractions_predictor.name == 'Label fractions predictor'
    assert label_fractions_predictor.input_descriptor.key == 'formulation'
    assert label_fractions_predictor.labels == {'solvent'}
    expected_str = '<LabelFractionsPredictor \'Label fractions predictor\'>'
    assert str(label_fractions_predictor) == expected_str


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


def test_status(valid_label_fractions_predictor_data, auto_ml):
    """Ensure we can check the status of predictor validation."""
    # A locally built predictor should be "False" for all status checks
    assert not auto_ml.in_progress() and not auto_ml.failed() and not auto_ml.succeeded()
    # A deserialized predictor should have the correct status
    predictor = LabelFractionsPredictor.build(valid_label_fractions_predictor_data)
    assert predictor.succeeded() and not predictor.in_progress() and not predictor.failed()
