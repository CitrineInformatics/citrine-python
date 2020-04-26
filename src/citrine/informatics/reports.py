"""Tools for working with reports."""
from typing import Optional, Type, List, Dict, TypeVar
from abc import abstractmethod

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor

SelfType = TypeVar('SelfType', bound='Report')


class Report(PolymorphicSerializable['Report']):
    """[ALPHA] A Citrine Report contains information and performance metrics related to a module.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the only subtype."""
        return PredictorReport

    @classmethod
    def build(cls, data: dict) -> SelfType:
        """Build the underlying type."""
        subtype = cls.get_type(data)
        report = subtype.build(data)
        report.post_build()
        return report

    @abstractmethod
    def post_build(self):
        """Executes after a .build() is called in [[Report]]."""


class FeatureImportanceReport(Serializable["FeatureImportanceReport"]):
    """[ALPHA] Feature importances for a specific model response.

    Parameters
    ----------
    output_key: str
        key for the output
    importances: dict[str, float]
        feature importances

    """

    output_key = properties.String('response_key')
    importances = properties.Mapping(keys_type=properties.String, values_type=properties.Float,
                                     serialization_path='importances')

    def __init__(self, output_key: str, importances: Dict[str, float]):
        self.output_key = output_key
        self.importances = importances

    def __str__(self):
        return "<FeatureImportanceReport {!r}>".format(self.output_key)


class ModelSummary(Serializable['ModelSummary']):
    """[ALPHA] Summary of information about a single model in a predictor.

    Parameters
    ----------
    name: str
        the name of the model
    inputs: List[Descriptor]
        list of input descriptors
    outputs: List[Descriptor]
        list of output descriptors
    model_settings: dict
        settings of the model
    feature_importances: dict
        feature importances

    """

    name = properties.String('name')
    inputs = properties.List(properties.String(), 'inputs')
    outputs = properties.List(properties.String(), 'outputs')
    model_settings = properties.Raw('model_settings')
    feature_importances = properties.List(
        properties.Object(FeatureImportanceReport), 'feature_importances')

    def __init__(self,
                 name: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 model_settings,
                 feature_importances):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.model_settings = model_settings
        self.feature_importances = feature_importances

    def __str__(self):
        return '<ModelSummary {!r}>'.format(self.name)


class PredictorReport(Serializable['PredictorReport'], Report):
    """[ALPHA] The performance metrics corresponding to a predictor.

    Parameters
    ----------
    status: str
        the status of the report (e.g. PENDING, ERROR, OK, etc)
    descriptors: List[Descriptor]
        All descriptors that appear in the predictor
    model_summaries: List[ModelSummary]
        Summaries of all models in the predictor

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    status = properties.String('status')
    descriptors = properties.List(properties.Object(Descriptor), 'report.descriptors')
    model_summaries = properties.List(properties.Object(ModelSummary), 'report.models')
    # Structure model summary

    def __init__(self, status: str, descriptors: List[Descriptor],
                 model_summaries: List[ModelSummary], session: Optional[Session] = None):
        self.status = status
        self.descriptors = descriptors
        self.model_summaries = model_summaries
        self.session: Optional[Session] = session

    def post_build(self):
        for i, model in enumerate(self.model_summaries):
            for j, input_key in enumerate(model.inputs):
                self.model_summaries[i].inputs[j] = self._key_to_descriptor(input_key)
            for j, output_key in enumerate(model.outputs):
                self.model_summaries[i].outputs[j] = self._key_to_descriptor(output_key)

    def _key_to_descriptor(self, key: str) -> Descriptor:
        matching_descriptors = [d for d in self.descriptors if d.key == key]
        if len(matching_descriptors) == 1:
            return matching_descriptors[0]
        elif len(matching_descriptors) == 0:
            raise RuntimeError("blah")
        else:
            raise RuntimeError("blah")
