from typing import List
from uuid import uuid4
import pytest

from citrine.resources.project import Project
from citrine.resources.descriptors import DescriptorMethods
from citrine.informatics.descriptors import (
    Descriptor,
    RealDescriptor,
    CategoricalDescriptor,
    MolecularStructureDescriptor,
    ChemicalFormulaDescriptor,
    FormulationDescriptor
)
from citrine.informatics.predictors import (
    MolecularStructureFeaturizer,
    ChemicalFormulaFeaturizer,
    MeanPropertyPredictor,
    LabelFractionsPredictor,
    Predictor
)
from citrine.builders.predictors import build_mean_feature_property_predictors

from tests.utils.session import FakeSession


class FakeDescriptorMethods(DescriptorMethods):
    def __init__(self, num_properties):
        self.project_id = uuid4()
        self.session = FakeSession()
        self.num_properties = num_properties

    def from_predictor_responses(self, predictor: Predictor, inputs: List[Descriptor]):
        if isinstance(predictor, (MolecularStructureFeaturizer, ChemicalFormulaFeaturizer)):
            if isinstance(predictor, MolecularStructureFeaturizer):
                input_descriptor = predictor.descriptor
            else:
                input_descriptor = predictor.input_descriptor
            return [
                RealDescriptor(f"{input_descriptor.key} real property {i}", lower_bound=0, upper_bound=1, units="")
                       for i in range(self.num_properties)
            ] + [CategoricalDescriptor(f"{input_descriptor.key} categorical property", ["cat1", "cat2"])]

        elif isinstance(predictor, MeanPropertyPredictor):
            label_str = predictor.label or "all ingredients"
            return [
                RealDescriptor(
                    f"mean of {prop.key} for {label_str} in {predictor.input_descriptor.key}",
                    lower_bound=0,
                    upper_bound=1,
                    units=""
                )
                for prop in predictor.properties
            ]

class FakeProject(Project):
    def __init__(self, fake_descriptors: FakeDescriptorMethods):
        self.fake_descriptors = fake_descriptors

    @property
    def descriptors(self) -> DescriptorMethods:
        return self.fake_descriptors


def test_mean_feature_properties():
    num_properties = 3
    project = FakeProject(FakeDescriptorMethods(num_properties=num_properties))
    smiles = MolecularStructureDescriptor("smiles")
    chem = ChemicalFormulaDescriptor("formula")
    formulation = FormulationDescriptor("formulation")
    mol_featurizer = MolecularStructureFeaturizer(name="", description="", descriptor=smiles)
    chem_featurizer = ChemicalFormulaFeaturizer(name="", description="", input_descriptor=chem)

    for featurizer in [mol_featurizer, chem_featurizer]:
        # A standard case. Here we request one model for all ingredients and one for a label.
        models, outputs = build_mean_feature_property_predictors(
            project=project,
            featurizer=chem_featurizer,
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
    no_props_project = FakeProject(FakeDescriptorMethods(num_properties=0))
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
