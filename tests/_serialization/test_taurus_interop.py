from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.process_template import ProcessTemplate

from taurus.entity.bounds.categorical_bounds import CategoricalBounds
from taurus.util import flatten


def test_flatten():
    """Test that taurus utility methods can be applied to citrine-python objects.

    Citrine-python resources extend the taurus data model, so the taurus operations
    should work on them.
    """

    bounds = CategoricalBounds(categories=["foo", "bar"])
    template = ProcessTemplate(
        "spam",
        conditions=[(ConditionTemplate(name="eggs", bounds=bounds), bounds)]
    )
    spec = ProcessSpec(name="spec", template=template)

    flat = flatten(spec)
    assert len(flat) == 2, "Expected 2 flattened objects"
