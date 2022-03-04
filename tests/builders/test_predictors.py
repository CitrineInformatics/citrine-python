import pytest

from citrine.informatics.descriptors import (
    MolecularStructureDescriptor,
    ChemicalFormulaDescriptor,
    FormulationDescriptor
)
from citrine.informatics.predictors import (
    MolecularStructureFeaturizer,
    ChemicalFormulaFeaturizer,
    LabelFractionsPredictor,
)
from citrine.builders.predictors import build_mean_feature_property_predictors
from tests.utils.fakes import FakeProject


def test_mean_feature_properties():
    num_properties = 3
    project = FakeProject(num_properties=num_properties)
    smiles = MolecularStructureDescriptor("smiles")
    chem = ChemicalFormulaDescriptor("formula")
    formulation = FormulationDescriptor("formulation")
    mol_featurizer = MolecularStructureFeaturizer(name="", description="", input_descriptor=smiles)
    chem_featurizer = ChemicalFormulaFeaturizer(name="", description="", input_descriptor=chem)

    for featurizer in [mol_featurizer, chem_featurizer]:
        # A standard case. Here we request one model for all ingredients and one for a label.
        models, outputs = build_mean_feature_property_predictors(
            project=project,
            featurizer=featurizer,
            formulation_descriptor=formulation,
            p=7,
            impute_properties=False,
            make_all_ingredients_model=True,
            labels=["some label"]
        )

        assert len(outputs) == num_properties * 2
        assert len(models) == 2
        for model in models:
            assert model.p == 7
            assert model.impute_properties == False
            assert model.input_descriptor == formulation
            assert len(model.properties) == num_properties

    # It's not necessary for the models to be returned in this order,
    # but this is how the logic is currently set up.
    assert models[0].label is None
    assert models[1].label == "some label"


    # expect an error if the featurizer model is not of allowed type
    not_featurizer = LabelFractionsPredictor(name="", description="", input_descriptor=formulation, labels={"label"})
    with pytest.raises(TypeError):
        build_mean_feature_property_predictors(
            project=project,
            featurizer=not_featurizer,
            formulation_descriptor=formulation,
            p=1
        )

    # expect an error if there are no mean property models requested
    with pytest.raises(ValueError):
        build_mean_feature_property_predictors(
            project=project,
            featurizer=mol_featurizer,
            formulation_descriptor=formulation,
            p=1,
            make_all_ingredients_model=False,
            labels=None
        )

    # expect an error if the featurizer model returns no real properties
    no_props_project = FakeProject(num_properties = 0)
    with pytest.raises(RuntimeError):
        build_mean_feature_property_predictors(
            project=no_props_project,
            featurizer=mol_featurizer,
            formulation_descriptor=formulation,
            p=1
        )

    # expect an error if labels is not specified as a list
    with pytest.raises(TypeError):
        build_mean_feature_property_predictors(
            project=no_props_project,
            featurizer=mol_featurizer,
            formulation_descriptor=formulation,
            p=1,
            labels="not inside a list!"
        )
