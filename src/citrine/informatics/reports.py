"""Tools for working with reports."""
from typing import Optional, Type, List

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor


class Report(PolymorphicSerializable['Report']):
    """[ALPHA] A Citrine Report contains information and performance metrics related to a module.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the only subtype."""
        return PredictorReport


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
    feature_importances = properties.Raw('feature_importances')

    def __init__(self, name: str, inputs: List[Descriptor], outputs: List[Descriptor], model_settings, feature_importances):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.model_settings = model_settings
        self.feature_importances = feature_importances


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
    # Add post_build to turn descriptor keys into objects
    # Add objects for feature improtance
    # Structure model summary

    def __init__(self, status: str, descriptors: List[Descriptor],
                 model_summaries: List[ModelSummary], session: Optional[Session] = None):
        self.status = status
        self.descriptors = descriptors
        self.model_summaries = model_summaries
        self.session: Optional[Session] = session
