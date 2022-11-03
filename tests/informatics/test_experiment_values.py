import uuid

import pytest

from citrine.informatics.experiment_values import ExperimentValue, \
                                                  RealExperimentValue, \
                                                  IntegerExperimentValue, \
                                                  CategoricalExperimentValue, \
                                                  MixtureExperimentValue, \
                                                  ChemicalFormulaExperimentValue, \
                                                  MolecularStructureExperimentValue


@pytest.fixture(params=[
    CategoricalExperimentValue("categorical"),
    ChemicalFormulaExperimentValue("(Ca)1(O)3(Si)1"),
    IntegerExperimentValue(7),
    MixtureExperimentValue({"ingredient1": 0.3, "ingredient2": 0.7}),
    MolecularStructureExperimentValue("CC1(CC(CC(N1)(C)C)NCCCCCCNC2CC(NC(C2)(C)C)(C)C)C.C1COCCN1C2=NC(=NC(=N2)Cl)Cl"),
    RealExperimentValue(3.5)
])
def experiment_value(request):
    return request.param


def test_deser_from_parent(experiment_value):
    # Serialize and deserialize the experiment values, making sure they are round-trip serializable
    data = experiment_value.dump()
    experiment_value_deserialized = ExperimentValue.build(data)
    assert experiment_value == experiment_value_deserialized


def test_invalid_eq(experiment_value):
    other = None
    assert not experiment_value == other


def test_string_rep(experiment_value):
    """String representation of experiment value should contain the type and value."""
    assert str(experiment_value.value) in str(experiment_value)
    assert experiment_value.__class__.__name__ in str(experiment_value)
    assert str(experiment_value.value) in repr(experiment_value)
    assert experiment_value.__class__.__name__ in repr(experiment_value)
