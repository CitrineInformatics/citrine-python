from collections.abc import Mapping

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import (
    CategoricalDescriptor, FormulationDescriptor, RealDescriptor
)
from citrine.informatics.predictors import PredictorNode

__all__ = ['MeanPropertyPredictor']


class MeanPropertyPredictor(Resource["MeanPropertyPredictor"], PredictorNode):
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
    properties: list[RealDescriptor | CategoricalDescriptor]
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
    label: str | None
        Only ingredients with this label are counted when calculating the component-weighted mean.
        If ``None`` (default) all ingredients will be counted.
    default_properties: Mapping[str, str | float] | None
        Default values to use for imputed properties.
        Defaults are specified as a map from descriptor key to its default value.
        If not specified and ``impute_properties == True`` the average over the entire dataset
        will be used to fill in missing values. Any specified defaults will be used in place of
        the average over the dataset. ``impute_properties`` must be ``True`` if
        ``default_properties`` are provided.

    """

    input_descriptor = _properties.Object(FormulationDescriptor, 'input')
    properties = _properties.List(
        _properties.Union(
            [_properties.Object(RealDescriptor), _properties.Object(CategoricalDescriptor)]
        ),
        'properties'
    )
    p = _properties.Float('p')
    impute_properties = _properties.Boolean('impute_properties')
    label = _properties.Optional(_properties.String, 'label')
    default_properties = _properties.Optional(
        _properties.Mapping(
            _properties.String,
            _properties.Union([_properties.String, _properties.Float])
        ),
        'default_properties'
    )

    typ = _properties.String('type', default='MeanProperty', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 properties: list[RealDescriptor | CategoricalDescriptor],
                 p: float,
                 impute_properties: bool,
                 label: str | None = None,
                 default_properties: Mapping[str, str | float] | None = None):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.properties: list[RealDescriptor | CategoricalDescriptor] = properties
        self.p: float = p
        self.impute_properties: bool = impute_properties
        self.label: str | None = label
        self.default_properties: Mapping[str, str | float] | None = default_properties

    def __str__(self):
        return '<MeanPropertyPredictor {!r}>'.format(self.name)
