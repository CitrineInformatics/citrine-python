import pytest

from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.process_template import ProcessTemplate

from gemd.entity.bounds.categorical_bounds import CategoricalBounds
from gemd.util import flatten


def test_flatten():
    """Test that gemd utility methods can be applied to citrine-python objects.
    Citrine-python resources extend the gemd data model, so the gemd operations
    should work on them.
    """

    bounds = CategoricalBounds(categories=["foo", "bar"])
    template = ProcessTemplate(
        "spam",
        conditions=[(ConditionTemplate(name="eggs", bounds=bounds), bounds)]
    )
    spec = ProcessSpec(name="spec", template=template)

    flat = flatten(spec, scope='testing')
    assert len(flat) == 3, "Expected 3 flattened objects"


def test_mismatch():
    """Test behavior when we have type mismatch between a dict and target object."""
    spec = ProcessSpec(name="spec")
    assert spec == ProcessSpec.build(spec.dump())
    with pytest.raises(ValueError):
        ProcessTemplate.build(spec.dump())
