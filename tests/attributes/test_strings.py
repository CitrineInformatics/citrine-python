from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from citrine.attributes.property import Property
from citrine.attributes.property_and_conditions import PropertyAndConditions


def test_condition_string():
    assert "<Condition 'test condition'>" == str(Condition(name='test condition'))


def test_parameter_string():
    assert "<Parameter 'test param'>" == str(Parameter(name='test param'))


def test_property_and_conditions_string():
    prop = Property(name='test prop')
    conditions = [Condition(name='tc1'), Condition(name='tc2')]

    assert "<Property And Conditions 'test prop' and ['tc1', 'tc2']>" == str(PropertyAndConditions(prop, conditions))
