from typing import Mapping

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['ExpressionPredictor']


class ExpressionPredictor(VersionedEngineResource['ExpressionPredictor'], Predictor):
    """A predictor that computes an output from an expression and set of bounded inputs.

    For a discussion of expression syntax and a list of allowed symbols,
    please see the :ref:`documentation<Expression Predictor>`.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    expression: str
        expression that computes an output from aliased inputs
    output: RealDescriptor
        descriptor that represents the output of the expression
    aliases: Mapping[str, RealDescriptor]
        a mapping from each unknown argument to its descriptor.
        All unknown arguments must have an associated descriptor.

    """

    expression = _properties.String('data.instance.expression')
    output = _properties.Object(RealDescriptor, 'data.instance.output')
    aliases = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                  'data.instance.aliases')

    typ = _properties.String('data.instance.type',
                             default='AnalyticExpression', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 expression: str,
                 output: RealDescriptor,
                 aliases: Mapping[str, RealDescriptor]):
        self.name: str = name
        self.description: str = description
        self.expression: str = expression
        self.output: RealDescriptor = output
        self.aliases: Mapping[str, RealDescriptor] = aliases

    def __str__(self):
        return '<ExpressionPredictor {!r}>'.format(self.name)
