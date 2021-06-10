"""Tools for working with reports."""
from typing import Type, Dict, TypeVar, Iterable
from abc import abstractmethod
from itertools import groupby
import warnings

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._rest.asynchronous_object import AsynchronousObject
from citrine.informatics.descriptors import Descriptor

SelfType = TypeVar('SelfType', bound='Report')


class Report(PolymorphicSerializable['Report'], AsynchronousObject):
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
    """

    output_key = properties.String('response_key')
    """:str: output descriptor key for which these feature importances are applicable"""
    importances = properties.Mapping(keys_type=properties.String, values_type=properties.Float,
                                     serialization_path='importances')
    """:dict[str, float]: map from feature name to its importance"""

    def __init__(self):
        pass  # pragma: no cover

    def __str__(self):
        return "<FeatureImportanceReport {!r}>".format(self.output_key)  # pragma: no cover


class ModelSummary(Serializable['ModelSummary']):
    """[ALPHA] Summary of information about a single model in a predictor.

    ModelSummary objects are constructed from saved models and should not be user-instantiated.
    """

    name = properties.String('name')
    """:str: the name of the model"""
    type_ = properties.String('type')
    """:str: the type of the model (e.g., "ML Model", "Featurizer", etc.)"""
    inputs = properties.List(
        properties.Union([properties.Object(Descriptor), properties.String()]),
        'inputs'
    )
    """:List[Descriptor]: list of input descriptors"""
    outputs = properties.List(
        properties.Union([properties.Object(Descriptor), properties.String()]),
        'outputs'
    )
    """:List[Descriptor]: list of output descriptors"""
    model_settings = properties.Raw('model_settings')
    """:dict: model settings, as a dictionary (keys depend on the model type)"""
    feature_importances = properties.List(
        properties.Object(FeatureImportanceReport), 'feature_importances')
    """:List[FeatureImportanceReport]: feature importance reports for each output"""
    predictor_name = properties.String('predictor_configuration_name', default='')
    """:str: the name of the predictor that created this model"""
    predictor_uid = properties.Optional(properties.UUID(), 'predictor_configuration_uid')
    """:Optional[UUID]: the unique Citrine id of the predictor that created this model"""
    training_data_count = properties.Optional(properties.Integer, "training_data_count")
    """:int: Number of rows in the training data for the model, if applicable."""

    def __init__(self):
        pass  # pragma: no cover

    def __str__(self):
        return '<ModelSummary {!r}>'.format(self.name)  # pragma: no cover


class PredictorReport(Serializable['PredictorReport'], Report):
    """[ALPHA] The performance metrics corresponding to a predictor.

    PredictorReport objects are constructed from saved models and should not be user-instantiated.
    """

    _in_progress_statuses = ["PENDING"]
    _succeeded_statuses = ["OK"]
    _failed_statuses = ["ERROR"]

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    """:UUID: Unique Citrine id of the predictor report"""
    status = properties.String('status')
    """:str: The status of the report. Possible statuses are PENDING, ERROR, and OK."""
    descriptors = properties.List(properties.Object(Descriptor), 'report.descriptors', default=[])
    """:List[Descriptor]: All descriptors that appear in the predictor"""
    model_summaries = properties.List(properties.Object(ModelSummary), 'report.models', default=[])
    """:List[ModelSummary]: Summaries of all models in the predictor"""

    def __init__(self):
        pass  # pragma: no cover

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
