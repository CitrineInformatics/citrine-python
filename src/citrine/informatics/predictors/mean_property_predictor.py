from typing import List, Optional, Mapping

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
from citrine.informatics.predictors import Predictor
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['MeanPropertyPredictor']


class MeanPropertyPredictor(
        Resource['MeanPropertyPredictor'], Predictor, AIResourceMetadata):
    """A predictor interface that computes mean component properties.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    properties: List[RealDescriptor]
        List of descriptors to featurize
    p: int
        Power of the `generalized mean <https://en.wikipedia.org/wiki/Generalized_mean>`_.
        Only integer powers are supported.
    impute_properties: bool
        Whether to impute missing ingredient properties.
        If ``False`` all ingredients must define values for all featurized properties.
        Otherwise, the row will not be featurized.
        If ``True`` and no ``default_properties`` are specified, then the average over the
        entire dataset is used.
        If ``True`` and a default is specified in ``default_properties``, then the specified
        default is used in place of missing values.
    label: Optional[str]
        Only ingredients with this label will be counted in calculating the generalized mean.
        If ``None`` (default) all ingredients will be counted.
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. De-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.
    default_properties: Optional[Mapping[str, float]]
        Default values to use for imputed properties.
        Defaults are specified as a map from descriptor key to its default value.
        If not specified and ``impute_properties == True`` the average over the entire dataset
        will be used to fill in missing values. Any specified defaults will be used in place of
        the average over the dataset. ``impute_properties`` must be ``True`` if
        ``default_properties`` are provided.

    """

    _resource_type = ResourceTypeEnum.MODULE

    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    properties = _properties.List(_properties.Object(RealDescriptor), 'config.properties')
    p = _properties.Integer('config.p')
    training_data = _properties.List(_properties.Object(DataSource),
                                     'config.training_data', default=[])
    impute_properties = _properties.Boolean('config.impute_properties')
    default_properties = _properties.Optional(
        _properties.Mapping(_properties.String, _properties.Float), 'config.default_properties')
    label = _properties.Optional(_properties.String, 'config.label')

    typ = _properties.String('config.type', default='MeanProperty', deserializable=False)
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 properties: List[RealDescriptor],
                 p: int,
                 impute_properties: bool,
                 default_properties: Optional[Mapping[str, float]] = None,
                 label: Optional[str] = None,
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.properties: List[RealDescriptor] = properties
        self.p: int = p
        self.training_data: List[DataSource] = training_data or []
        self.impute_properties: bool = impute_properties
        self.default_properties: Optional[Mapping[str, float]] = default_properties
        self.label: Optional[str] = label

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<MeanPropertyPredictor {!r}>'.format(self.name)
