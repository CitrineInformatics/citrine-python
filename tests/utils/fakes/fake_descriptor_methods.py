from typing import List
from uuid import uuid4

from citrine.informatics.descriptors import Descriptor, RealDescriptor, CategoricalDescriptor
from citrine.informatics.predictors import Predictor, ChemicalFormulaFeaturizer, MolecularStructureFeaturizer, \
    MeanPropertyPredictor
from citrine.resources.descriptors import DescriptorMethods
from tests.utils.session import FakeSession


class FakeDescriptorMethods(DescriptorMethods):
    def __init__(self, num_properties):
        self.project_id = uuid4()
        self.session = FakeSession()
        self.num_properties = num_properties

    def from_predictor_responses(self, predictor: Predictor, inputs: List[Descriptor]):
        if isinstance(predictor, (MolecularStructureFeaturizer, ChemicalFormulaFeaturizer)):
            input_descriptor = predictor.input_descriptor
            return [
                       RealDescriptor(f"{input_descriptor.key} real property {i}", lower_bound=0, upper_bound=1, units="")
                       for i in range(self.num_properties)
                   ] + [CategoricalDescriptor(f"{input_descriptor.key} categorical property", categories=["cat1", "cat2"])]

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