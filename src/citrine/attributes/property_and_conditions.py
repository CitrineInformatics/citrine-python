"""A resource that represents a property_and_conditions compound attribute."""
from typing import Optional, List

from citrine._serialization.properties import Object, String
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.serializable import Serializable
from citrine.resources.data_concepts import DataConcepts
from citrine.attributes.condition import Condition
from citrine.attributes.property import Property
from taurus.entity.attribute.property_and_conditions import PropertyAndConditions \
    as TaurusPropertyAndConditions


class PropertyAndConditions(DataConcepts, Serializable['PropertyAndConditions'],
                            TaurusPropertyAndConditions):
    """
    A compound attribute with one property and a list of relevant conditions.

    In the MaterialSpec object, one may need to specify a property along with the conditions
    under which the property occurs. For example:

    * Vapor pressure of 5.6 kPa at a temperature of 35 deg C
    * Gas phase at a pressure of 1 kPa and a temperature of 300 K

    Parameters
    ----------
    property: :class:`Property <citrine.attributes.property.Property>`
        A property attribute
    conditions: List[:class:`Condition <citrine.attributes.condition.Condition>`]
        An optional list of conditions associated with this property

    """

    _response_key = TaurusPropertyAndConditions.typ  # 'property_and_conditions'

    property = Object(Property, 'property')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    typ = String('type', default=_response_key, deserializable=False)

    def __init__(self,
                 property: Property,
                 conditions: Optional[List[Condition]] = []):
        TaurusPropertyAndConditions.__init__(self, property=property, conditions=conditions)

    def __str__(self):
        return '<Property And Conditions ' \
               '{!r} and {!r}>'.format(self.property.name,
                                       [cond.name for cond in self.conditions])
