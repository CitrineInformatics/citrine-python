from typing import Optional, Mapping
from warnings import warn

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['ExpressionPredictor', 'DeprecatedExpressionPredictor']


class ExpressionPredictor(Serializable['ExpressionPredictor'], Predictor):
    """A predictor that computes an output from an expression and set of bounded inputs.

    .. seealso::
       If you are using the deprecated predictor please see
       :class:`~citrine.informatics.predictors.DeprecatedExpressionPredictor` for an example that
       shows how to migrate to the new format.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    expression: str
        expression that computes an output from aliased inputs
    output: RealDescriptor
        descriptor that represents the output relation
    aliases: Mapping[str, RealDescriptor]
        a mapping from each unknown argument to its descriptor.
        All unknown arguments must have an associated descriptor.

    """

    expression = _properties.String('config.expression')
    output = _properties.Object(RealDescriptor, 'config.output')
    aliases = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                  'config.aliases')
    typ = _properties.String('config.type', default='AnalyticExpression', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 expression: str,
                 output: RealDescriptor,
                 aliases: Mapping[str, RealDescriptor],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.expression: str = expression
        self.output: RealDescriptor = output
        self.aliases: Mapping[str, RealDescriptor] = aliases
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ExpressionPredictor {!r}>'.format(self.name)


class DeprecatedExpressionPredictor(Serializable['DeprecatedExpressionPredictor'], Predictor):
    """[DEPRECATED] A predictor that computes an output from an analytic expression.

    This predictor is deprecated. Please use the
    :class:`~citrine.informatics.predictors.ExpressionPredictor` instead.
    To migrate to the new predictor:

    1. add an alias for all unknown expression arguments and
    2. replace descriptor keys in ``aliases`` with the associated descriptor

    These changes allow the expression to respect descriptor bounds when computing the output and
    avoid potential descriptor mismatches if a descriptor with an identical key and different
    bounds is present in the graph.

    The following example shows how to migrate a deprecated expression predictor to the new format.
    In the deprecated format, an expression that computes shear modulus from Young's modulus and
    Poisson's ratio is given by:

    .. code-block:: python

       from citrine.informatics.predictors import DeprecatedExpressionPredictor

       shear_modulus = RealDescriptor(
           'Property~Shear modulus',
           lower_bound=0,
           upper_bound=100,
           units='GPa'
        )

       shear_modulus_predictor = DeprecatedExpressionPredictor(
           name = 'Shear modulus predictor',
           description = "Computes shear modulus from Young's modulus and Poisson's ratio.",
           expression = 'Y / (2 * (1 + v))',
           output = shear_modulus,
           aliases = {
               'Y': "Young's modulus",
               'v': "Poisson's ratio"
           }
       )

    To create a predictor using the format, we need to create descriptors for the expression
    inputs: Young's modulus and Poisson's ratio. We also need to replace references to the
    descriptor keys in ``aliases`` with the new descriptors:

    .. code-block:: python

       from citrine.informatics.predictors import ExpressionPredictor

       # create a descriptor for each input in addition to the output
       youngs_modulus = RealDescriptor('Property~Young\'s modulus', lower_bound=0,
                                       upper_bound=100, units='GPa')
       poissons_ratio = RealDescriptor('Property~Poisson\'s ratio', lower_bound=-1,
                                       upper_bound=0.5, units='')
       shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0,
                                      upper_bound=100, units='GPa')

       shear_modulus_predictor = ExpressionPredictor(
           name = 'Shear modulus predictor',
           description = "Computes shear modulus from Young's modulus and Poisson's ratio.",
           expression = 'Y / (2 * (1 + v))',
           output = shear_modulus,
           # note, arguments map to descriptors not descriptor keys
           aliases = {
               'Y': youngs_modulus,
               'v': poissons_ratio
           }
       )

    .. seealso:: :class:`~citrine.informatics.predictors.ExpressionPredictor`

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    expression: str
        expression that computes an output from a set of inputs
    output: RealDescriptor
        descriptor that represents the output of the expression
    aliases: Optional[Mapping[str, str]]
        a mapping from each each argument as it appears in the ``expression`` to its descriptor
        key. If an unknown argument is not aliased, the argument and descriptor key are assumed
        to be identical.

    """

    expression = _properties.String('config.expression')
    output = _properties.Object(RealDescriptor, 'config.output')
    aliases = _properties.Optional(_properties.Mapping(_properties.String, _properties.String),
                                   'config.aliases')
    typ = _properties.String('config.type', default='Expression', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 expression: str,
                 output: RealDescriptor,
                 aliases: Optional[Mapping[str, str]] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        warn("{this_class} is deprecated. Please use {replacement} instead"
             .format(this_class=self.__class__.name, replacement=ExpressionPredictor.__name__))
        self.name: str = name
        self.description: str = description
        self.expression: str = expression
        self.output: RealDescriptor = output
        self.aliases: Optional[Mapping[str, str]] = aliases
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<DeprecatedExpressionPredictor {!r}>'.format(self.name)
