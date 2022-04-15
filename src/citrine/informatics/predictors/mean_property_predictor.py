from typing import List, Optional, Mapping, Union

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import (
    FormulationDescriptor, RealDescriptor, CategoricalDescriptor
)
from citrine.informatics.predictors import Predictor

__all__ = ['MeanPropertyPredictor']


class MeanPropertyPredictor(
        EngineResource['MeanPropertyPredictor'], Predictor):
    """A predictor that computes a component-weighted mean of real or categorical properties.

    Each component in a formulation contributes to the mean property
    a weight equal to its quantity raised to the power `p`.
    For real-valued properties, the property values of each component are averaged
    with these weights to yield the component-weighted mean property.
    For categorical-valued properties, these weights are accumulated to yield a
    distribution over property values in the formulation.

    Parameters
    ----------
    name: str
        Name of the configuration
    description: str
        Description of the predictor
    input_descriptor: FormulationDescriptor
        Descriptor that represents the input formulation
    properties: List[Union[RealDescriptor, CategoricalDescriptor]]
        List of real or categorical descriptors to featurize
    p: float
        Power of the component-weighted mean.
        Positive, negative, and fractional powers are supported.
    impute_properties: bool
        Whether to impute missing ingredient properties.
        If ``False`` all ingredients must define values for all featurized properties.
        Otherwise, the row will not be featurized.
        If ``True`` and no ``default_properties`` are specified, then the average over the
        entire dataset is used.
        If ``True`` and a default is specified in ``default_properties``, then the specified
        default is used in place of missing values.
    label: Optional[str]
        Only ingredients with this label are counted when calculating the component-weighted mean.
        If ``None`` (default) all ingredients will be counted.
    default_properties: Optional[Mapping[str, Union[str, float]]]
        Default values to use for imputed properties.
        Defaults are specified as a map from descriptor key to its default value.
        If not specified and ``impute_properties == True`` the average over the entire dataset
        will be used to fill in missing values. Any specified defaults will be used in place of
        the average over the dataset. ``impute_properties`` must be ``True`` if
        ``default_properties`` are provided.
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. De-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'data.instance.input')
    properties = _properties.List(
        _properties.Union(
            [_properties.Object(RealDescriptor), _properties.Object(CategoricalDescriptor)]
        ),
        'data.instance.properties'
    )
    p = _properties.Float('data.instance.p')
    impute_properties = _properties.Boolean('data.instance.impute_properties')
    label = _properties.Optional(_properties.String, 'data.instance.label')
    default_properties = _properties.Optional(
        _properties.Mapping(
            _properties.String,
            _properties.Union([_properties.String, _properties.Float])
        ),
        'data.instance.default_properties'
    )
    training_data = _properties.List(
        _properties.Object(DataSource), 'data.instance.training_data', default=[]
    )

    typ = _properties.String('data.instance.type', default='MeanProperty', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 properties: List[Union[RealDescriptor, CategoricalDescriptor]],
                 p: float,
                 impute_properties: bool,
                 label: Optional[str] = None,
                 default_properties: Optional[Mapping[str, Union[str, float]]] = None,
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.properties: List[Union[RealDescriptor, CategoricalDescriptor]] = properties
        self.p: float = p
        self.impute_properties: bool = impute_properties
        self.label: Optional[str] = label
        self.default_properties: Optional[Mapping[str, Union[str, float]]] = default_properties
        self.training_data: List[DataSource] = training_data or []

    def __str__(self):
        return '<MeanPropertyPredictor {!r}>'.format(self.name)
