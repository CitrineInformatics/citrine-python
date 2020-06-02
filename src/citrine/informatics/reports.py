"""Tools for working with reports."""
from typing import Optional, Type, List, Dict, TypeVar, Iterable, Any
from abc import abstractmethod
from itertools import groupby
import warnings
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor

SelfType = TypeVar('SelfType', bound='Report')


class Report(PolymorphicSerializable['Report']):
    """[ALPHA] A Citrine Report contains information related to a module.

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

    FeatureImportanceReport objects are constructed from saved models and
    should not be user-instantiated.

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

    ModelSummary objects are constructed from saved models and should not be user-instantiated.

    Parameters
    ----------
    name: str
        the name of the model
    type_: str
        the type of the model (e.g., "ML Model", "Featurizer", etc.)
    inputs: List[Descriptor]
        list of input descriptors
    outputs: List[Descriptor]
        list of output descriptors
    model_settings: dict
        settings of the model, as a dictionary (details depend on model type)
    feature_importances: List[FeatureImportanceReport]
        list of feature importance reports, one for each output
    predictor_name: str
        the name of the predictor that created this model
    predictor_uid: Optional[uuid]
        the uid of the predictor that created this model

    """

    name = properties.String('name')
    type_ = properties.String('type')
    inputs = properties.List(properties.String(), 'inputs')
    outputs = properties.List(properties.String(), 'outputs')
    model_settings = properties.Raw('model_settings')
    feature_importances = properties.List(
        properties.Object(FeatureImportanceReport), 'feature_importances')
    predictor_name = properties.String('predictor_configuration_name', default='')
    predictor_uid = properties.Optional(properties.UUID(), 'predictor_configuration_uid')

    def __init__(self,
                 name: str,
                 type_: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 model_settings: Dict[str, Any],
                 feature_importances: List[FeatureImportanceReport],
                 predictor_name: str,
                 predictor_uid: Optional[UUID] = None):
        self.name = name
        self.type_ = type_
        self.inputs = inputs
        self.outputs = outputs
        self.model_settings = model_settings
        self.feature_importances = feature_importances
        self.predictor_name = predictor_name
        self.predictor_uid = predictor_uid

    def __str__(self):
        return '<ModelSummary {!r}>'.format(self.name)


class PredictorReport(Serializable['PredictorReport'], Report):
    """[ALPHA] The performance metrics corresponding to a predictor.

    PredictorReport objects are constructed from saved models and should not be user-instantiated.

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
    descriptors = properties.List(properties.Object(Descriptor), 'report.descriptors', default=[])
    model_summaries = properties.List(properties.Object(ModelSummary), 'report.models', default=[])

    def __init__(self, status: str,
                 descriptors: Optional[List[Descriptor]] = None,
                 model_summaries: Optional[List[ModelSummary]] = None,
                 session: Optional[Session] = None):
        self.status = status
        self.descriptors = descriptors or []
        self.model_summaries = model_summaries or []
        self.session: Optional[Session] = session

    def post_build(self):
        """Modify a PredictorReport object in-place after deserialization."""
        self._fill_out_descriptors()
        for _, model in enumerate(self.model_summaries):
            self._collapse_model_settings(model)

    def _fill_out_descriptors(self):
        """Replace descriptor keys in `model_summaries` with full Descriptor objects."""
        descriptor_map = dict()
        for key, group in groupby(sorted(self.descriptors, key=lambda d: d.key), lambda d: d.key):
            descriptor_map[key] = self._get_sole_descriptor(group)
        for i, model in enumerate(self.model_summaries):
            for j, input_key in enumerate(model.inputs):
                try:
                    model.inputs[j] = descriptor_map[input_key]
                except KeyError:
                    raise RuntimeError("Model {} contains input \'{}\', but no descriptor found "
                                       "with that key".format(model.name, input_key))
            for j, output_key in enumerate(model.outputs):
                try:
                    model.outputs[j] = descriptor_map[output_key]
                except KeyError:
                    raise RuntimeError("Model {} contains output \'{}\', but no descriptor found "
                                       "with that key".format(model.name, input_key))

    @staticmethod
    def _get_sole_descriptor(it: Iterable):
        """Get what should be the sole descriptor in an iterable of descriptors.

        This method is called by `_fill_out_descriptors` on an iterable of descriptors
        that have been grouped by their key.

        Parameters
        ----------
        it: Iterable
            iterable of descriptors

        """
        as_list = list(it)
        if len(as_list) > 1:
            serialized_descriptors = [d.dump() for d in as_list]
            warnings.warn("Warning: found multiple descriptors with the key \'{}\', arbitrarily "
                          "selecting the first one. The descriptors are: {}"
                          .format(as_list[0].key, serialized_descriptors), RuntimeWarning)
        return as_list[0]

    @staticmethod
    def _collapse_model_settings(model: ModelSummary):
        """Collapse a model's settings into a flat dictionary.

        Model settings are returned as a dictionary with a "name" field, a "value" field,
        and "children," a list of sub-settings. This method flattens that structure to a
        top-level dictionary with keys given by "name" and values given by "value."

        """
        def _recurse_model_settings(settings: Dict[str, str], list_or_dict):
            """Recursively traverse the model settings, adding name-value pairs to dictionary."""
            if isinstance(list_or_dict, list):
                for setting in list_or_dict:
                    _recurse_model_settings(settings, setting)
            elif isinstance(list_or_dict, dict):
                settings[list_or_dict['name']] = list_or_dict['value']
                _recurse_model_settings(settings, list_or_dict['children'])

        settings = dict()
        _recurse_model_settings(settings, model.model_settings)
        model.model_settings = settings
