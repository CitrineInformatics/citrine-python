from typing import List, Optional, Mapping

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['GeneralizedMeanPropertyPredictor']


class GeneralizedMeanPropertyPredictor(
        Serializable['GeneralizedMeanPropertyPredictor'], Predictor):
    """[ALPHA] A predictor interface that computes generalized mean component properties.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    properties: List[str]
        List of component properties to featurize
    p: float
        Power of the generalized mean
    impute_properties: bool
        Whether to impute missing ingredient properties.
        If ``False`` an error is thrown when a missing ingredient property is encountered.
        If ``True`` and no ``default_properties`` are specified, then the average over the
        entire dataset is used.
        If ``True`` and a default is specified in ``default_properties``, then the specified
        default is used in place of missing values.
    label: Optional[str]
        Optional label
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and deduplicated by uid and
        identifiers. Deduplication is performed if a uid or identifier is shared between two or
        more rows. The content of a deduplicated row will contain the union of data across all rows
        that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.
    default_properties: Optional[Mapping[str, float]]
        Default values to use for imputed properties.
        Defaults are specified as a map from descriptor key to its default value.
        If not specified and ``impute_properties == True`` the average over the entire dataset
        will be used to fill in missing values. Any specified defaults will be used in place of
        the average over the dataset. ``impute_properties`` must be ``True`` if
        ``default_properties`` are provided.

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    properties = _properties.List(_properties.String, 'config.properties')
    p = _properties.Float('config.p')
    training_data = _properties.List(_properties.Object(DataSource), 'config.training_data')
    impute_properties = _properties.Boolean('config.impute_properties')
    default_properties = _properties.Optional(
        _properties.Mapping(_properties.String, _properties.Float), 'config.default_properties')
    label = _properties.Optional(_properties.String, 'config.label')
    typ = _properties.String('config.type', default='GeneralizedMeanProperty',
                             deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 properties: List[str],
                 p: float,
                 impute_properties: bool,
                 default_properties: Optional[Mapping[str, float]] = None,
                 label: Optional[str] = None,
                 training_data: Optional[List[DataSource]] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.properties: List[str] = properties
        self.p: float = p
        self.training_data: List[DataSource] = self._wrap_training_data(training_data)
        self.impute_properties: bool = impute_properties
        self.default_properties: Optional[Mapping[str, float]] = default_properties
        self.label: Optional[str] = label
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<GeneralizedMeanPropertyPredictor {!r}>'.format(self.name)
