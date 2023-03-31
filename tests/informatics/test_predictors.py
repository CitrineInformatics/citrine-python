"""Tests for citrine.informatics.predictors."""
import uuid
import pytest
import mock

from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor, IntegerDescriptor, \
    MolecularStructureDescriptor, FormulationDescriptor, ChemicalFormulaDescriptor, \
    CategoricalDescriptor, FormulationKey
from citrine.informatics.predictors import *
from citrine.informatics.predictors.single_predict_request import SinglePredictRequest
from citrine.informatics.predictors.single_prediction import SinglePrediction
from citrine.informatics.design_candidate import DesignMaterial

from tests.utils.factories import PredictorEntityDataFactory, PredictorDataDataFactory


w = IntegerDescriptor("w", lower_bound=0, upper_bound=100)
x = RealDescriptor("x", lower_bound=0, upper_bound=100, units="")
y = RealDescriptor("y", lower_bound=0, upper_bound=100, units="")
z = RealDescriptor("z", lower_bound=0, upper_bound=100, units="")
density = RealDescriptor('density', lower_bound=0, upper_bound=100, units='g/cm^3')
shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')
youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
chain_type = CategoricalDescriptor('Chain Type', categories={'Gaussian Coil', 'Rigid Rod', 'Worm-like'})
flat_formulation = FormulationDescriptor.flat()
water_quantity = RealDescriptor('water quantity', lower_bound=0, upper_bound=1, units="")
salt_quantity = RealDescriptor('salt quantity', lower_bound=0, upper_bound=1, units="")
data_source = GemTableDataSource(table_id=uuid.UUID('e5c51369-8e71-4ec6-b027-1f92bdc14762'), table_version=0)
formulation_data_source = GemTableDataSource(table_id=uuid.UUID('6894a181-81d2-4304-9dfa-a6c5b114d8bc'), table_version=0)


def build_predictor_data(instance):
    return dict(
        name=instance.get("name"),
        description=instance.get("description"),
        instance=instance
    )


def build_predictor_entity(data):
    user = str(uuid.uuid4())
    time = '2020-04-23T15:46:26Z'
    return dict(
        id=str(uuid.uuid4()),
        data=data,
        metadata=dict(
            status=dict(
                name='READY',
                info=[]
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
        description='Predicts z from inputs w and x',
        inputs=[w, x],
        outputs=[z],
        training_data=[data_source]
    )


@pytest.fixture
def auto_ml_no_outputs() -> AutoMLPredictor:
    return AutoMLPredictor(
        name='AutoML Predictor',
        description='Predicts z from inputs w and x',
        inputs=[w, x],
        outputs=[],
        training_data=[data_source]
    )


@pytest.fixture
def auto_ml_multiple_outputs() -> AutoMLPredictor:
    return AutoMLPredictor(
        name='AutoML Predictor',
        description='Predicts z from inputs w and x',
        inputs=[w, x],
        outputs=[z, y],
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
        input_descriptor=flat_formulation,
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
        training_data=[formulation_data_source]
    )


@pytest.fixture
def label_fractions_predictor() -> LabelFractionsPredictor:
    """Build a label fractions predictor for testing"""
    return LabelFractionsPredictor(
        name='Label fractions predictor',
        description='Compute relative proportions of labeled ingredients',
        input_descriptor=flat_formulation,
        labels={'solvent'}
    )


@pytest.fixture
def ingredient_fractions_predictor() -> IngredientFractionsPredictor:
    """Build a Ingredient Fractions predictor for testing."""
    return IngredientFractionsPredictor(
        name='Ingredient fractions predictor',
        description='Computes total ingredient fractions',
        input_descriptor=flat_formulation,
        ingredients={"Green Paste", "Blue Paste"}
    )


def test_simple_report(auto_ml):
    """Ensures we get a report from a simple predictor post_build call"""
    with pytest.raises(ValueError):
        # without a project or session, this should error
        assert auto_ml.report is None
    session = mock.Mock()
    session.get_resource.return_value = dict(status='OK', report=dict(descriptors=[], models=[]), uid=str(uuid.uuid4()))
    auto_ml._session = session
    auto_ml._project_id = uuid.uuid4()
    auto_ml.uid = uuid.uuid4()
    auto_ml.version = 2
    assert auto_ml.report is not None
    assert session.get_resource.call_count == 1
    assert auto_ml.report.status == 'OK'


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

    assert molecule_featurizer.dump() == PredictorDataDataFactory(instance={
            'name': 'Molecule featurizer',
            'description': 'description',
            'descriptor': {'descriptor_key': 'SMILES', 'type': 'Organic'},
            'features': ['all'],
            'excludes': ['standard'],
            'type': 'MoleculeFeaturizer'
        })


def test_chemical_featurizer(chemical_featurizer):
    assert chemical_featurizer.name == "Chemical featurizer"
    assert chemical_featurizer.description == "description"
    assert chemical_featurizer.input_descriptor == ChemicalFormulaDescriptor("formula")
    assert chemical_featurizer.features == ["standard"]
    assert chemical_featurizer.excludes == []
    assert chemical_featurizer.powers == [1, 2]

    assert str(chemical_featurizer) == "<ChemicalFormulaFeaturizer 'Chemical featurizer'>"

    assert chemical_featurizer.dump() == PredictorDataDataFactory(instance={
        'name': 'Chemical featurizer',
        'description': 'description',
        'input': ChemicalFormulaDescriptor("formula").dump(),
        'features': ['standard'],
        'excludes': [],
        'powers': [1, 2],
        'type': 'ChemicalFormulaFeaturizer'
    })


def test_auto_ml(auto_ml):
    assert auto_ml.name == "AutoML Predictor"
    assert auto_ml.description == "Predicts z from inputs w and x"
    assert auto_ml.inputs == [w, x]
    assert auto_ml.training_data == [data_source]
    assert auto_ml.dump()['instance']['outputs'] == [z.dump()]

    assert str(auto_ml) == "<AutoMLPredictor 'AutoML Predictor'>"

    built = AutoMLPredictor.build(PredictorEntityDataFactory(data=auto_ml.dump()))
    assert built.outputs == [z]
    assert built.dump()['instance']['outputs'] == [z.dump()]


def test_auto_ml_no_outputs(auto_ml_no_outputs):
    assert auto_ml_no_outputs.outputs == []
    assert auto_ml_no_outputs.dump()['instance']['outputs'] == []

    built = AutoMLPredictor.build(PredictorEntityDataFactory(data=auto_ml_no_outputs.dump()))
    assert built.outputs == []
    assert built.dump()['instance']['outputs'] == []


def test_auto_ml_estimators():
    # Check an empty set is coerced to RF default
    empty_aml = AutoMLPredictor(
        name="",
        description="",
        inputs=[x],
        outputs=[y],
        estimators={}
    )
    assert empty_aml.estimators == {AutoMLEstimator.RANDOM_FOREST}

    # Check passing invalid strings leads to an error
    with pytest.raises(ValueError):
        AutoMLPredictor(
            name="",
            description="",
            inputs=[x],
            outputs=[y],
            estimators={"pancakes"}
        )


def test_auto_ml_multiple_outputs(auto_ml_multiple_outputs):
    assert auto_ml_multiple_outputs.outputs == [z, y]
    assert auto_ml_multiple_outputs.dump()['instance']['outputs'] == [z.dump(), y.dump()]

    built = AutoMLPredictor.build(PredictorEntityDataFactory(data=auto_ml_multiple_outputs.dump()))
    assert built.outputs == [z, y]
    assert built.dump()['instance']['outputs'] == [z.dump(), y.dump()]


def test_ing_to_formulation_initialization(ing_to_formulation_predictor):
    """Make sure the correct fields go to the correct places for an ingredients to formulation predictor."""
    assert ing_to_formulation_predictor.name == 'Ingredients to formulation predictor'
    assert ing_to_formulation_predictor.output.key == FormulationKey.HIERARCHICAL.value
    assert ing_to_formulation_predictor.id_to_quantity == {'water': water_quantity, 'salt': salt_quantity}
    assert ing_to_formulation_predictor.labels == {'solvent': {'water'}, 'solute': {'salt'}}
    expected_str = f'<IngredientsToFormulationPredictor \'{ing_to_formulation_predictor.name}\'>'
    assert str(ing_to_formulation_predictor) == expected_str


def test_mean_property_initialization(mean_property_predictor):
    """Make sure the correct fields go to the correct places for a mean property predictor."""
    assert mean_property_predictor.name == 'Mean property predictor'
    assert mean_property_predictor.input_descriptor.key == FormulationKey.FLAT.value
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
    data = PredictorEntityDataFactory(data=mean_property_predictor.dump())
    new_mpp = MeanPropertyPredictor.build(data)
    real_props = [d for d in new_mpp.properties if isinstance(d, RealDescriptor)]
    cat_props = [d for d in new_mpp.properties if isinstance(d, CategoricalDescriptor)]
    assert len(new_mpp.properties) == 2
    assert len(real_props) == 1
    assert len(cat_props) == 1


def test_label_fractions_property_initialization(label_fractions_predictor):
    """Make sure the correct fields go to the correct places for a label fraction predictor."""
    assert label_fractions_predictor.name == 'Label fractions predictor'
    assert label_fractions_predictor.input_descriptor.key == FormulationKey.FLAT.value
    assert label_fractions_predictor.labels == {'solvent'}
    expected_str = '<LabelFractionsPredictor \'Label fractions predictor\'>'
    assert str(label_fractions_predictor) == expected_str


def test_simple_mixture_predictor_initialization(simple_mixture_predictor):
    """Make sure the correct fields go to the correct places for a simple mixture predictor."""
    assert simple_mixture_predictor.name == 'Simple mixture predictor'
    assert simple_mixture_predictor.input_descriptor.key == FormulationKey.HIERARCHICAL.value
    assert simple_mixture_predictor.output_descriptor.key == FormulationKey.FLAT.value
    assert simple_mixture_predictor.training_data == [formulation_data_source]
    expected_str = '<SimpleMixturePredictor \'Simple mixture predictor\'>'
    assert str(simple_mixture_predictor) == expected_str


def test_ingredient_fractions_property_initialization(ingredient_fractions_predictor):
    """Make sure the correct fields go to the correct places for an ingredient fractions predictor."""
    assert ingredient_fractions_predictor.name == 'Ingredient fractions predictor'
    assert ingredient_fractions_predictor.input_descriptor.key == FormulationKey.FLAT.value
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

def test_single_predict(graph_predictor):
    """Ensures we get a prediction back from a simple predict call"""
    session = mock.Mock()
    graph_predictor._project_id = uuid.uuid4()
    graph_predictor.uid = uuid.uuid4()
    graph_predictor.version = 2
    material_data = {'vars':
                     {'X': {'m': 1.1, 's': 0.1, 'type': 'R'},
                      'Y': {'m': 2.2, 's': 0.2, 'type': 'R'}}}
    material = DesignMaterial.build(material_data)
    request = SinglePredictRequest(uuid.uuid4(), list(), material)
    prediction_in = SinglePrediction(request.material_id, list(), material)
    session.post_resource.return_value = prediction_in.dump()
    graph_predictor._session = session
    prediction_out = graph_predictor.predict(request)
    assert prediction_out.dump() == prediction_in.dump()
    assert session.post_resource.call_count == 1


def test_formulation_deprecations():
    with pytest.warns(DeprecationWarning):
        SimpleMixturePredictor(
            name="Warning",
            description="Description",
            input_descriptor=FormulationDescriptor.hierarchical(),
            output_descriptor=FormulationDescriptor.flat()
        )
    with pytest.warns(DeprecationWarning):
        IngredientsToFormulationPredictor(
            name="Warning",
            description="Description",
            output=FormulationDescriptor.hierarchical(),
            id_to_quantity={},
            labels={}
        )
