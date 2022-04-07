import pytest

from citrine._utils.batcher import Batcher

from gemd.demo.cake import make_cake
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object import *
from gemd.entity.template import *
from gemd.util import flatten, writable_sort_order


def test_by_type():
    """Test type batching."""
    batcher = Batcher.by_type()
    cake = make_cake()
    first = batcher.batch(flatten(cake), batch_size=10)
    assert all(len(batch) <= 10 for batch in first), "A batch was too long"
    for i in range(len(first) - 1):
        assert max(writable_sort_order(x) for x in first[i]) \
               <= min(writable_sort_order(x) for x in first[i+1]), "Load order violated"
    assert len(flatten(cake)) == len({y for x in first for y in x}), "Object missing"
    assert len(flatten(cake)) == len([y for x in first for y in x]), "Object repeated"

    second = batcher.batch(flatten(cake), batch_size=20)
    assert any(len(batch) > 10 for batch in second)  # batch_size matters

    third = batcher.batch(flatten(cake) + flatten(cake), batch_size=10)
    assert third == first, "Replicates changed the batching"

    with pytest.raises(ValueError):
        bad = [
            ProcessSpec(name="One", uids={"bad": "id"}),
            ProcessSpec(name="Two", uids={"bad": "id"})
        ]
        batcher.batch(bad, batch_size=10)


def test_by_dependency():
    batcher = Batcher.by_dependency()
    cake = make_cake()

    first = batcher.batch(flatten(cake), batch_size=30)
    assert all(len(batch) <= 30 for batch in first), "A batch was too long"
    assert len(flatten(cake)) == len({y for x in first for y in x}), "Object missing"

    for batch in first:
        derefs = {obj: obj for obj in batch}
        # Index LinkByUIDs
        for obj in batch:
            for this_scope in obj.uids:
                derefs[LinkByUID.from_entity(obj, scope=this_scope)] = obj
        derefs[None] = None  # It's fine if the attribute didn't reference a template

        # Note we flattened, so all refs should be LinkByUIDs
        for obj in batch:
            if isinstance(obj, ProcessTemplate):
                for x in obj.parameters:
                    assert x[0] in derefs, "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert x[0] in derefs, "Referenced condition wasn't in batch"
            elif isinstance(obj, MaterialTemplate):
                for x in obj.properties:
                    assert x[0] in derefs
            elif isinstance(obj, MeasurementTemplate):
                for x in obj.parameters:
                    assert x[0] in derefs, "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert x[0] in derefs, "Referenced condition wasn't in batch"
                for x in obj.properties:
                    assert x[0] in derefs, "Referenced property wasn't in batch"
            elif isinstance(obj, ProcessSpec):
                assert obj.template in derefs, "Template wasn't in batch"
                for x in obj.parameters:
                    assert x.template in derefs, "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert x.template in derefs, "Referenced condition wasn't in batch"
            elif isinstance(obj, ProcessRun):
                assert obj.spec in derefs, "Spec wasn't in batch"
                for x in obj.parameters:
                    assert(x.template in derefs), "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert(x.template in derefs), "Referenced condition wasn't in batch"
            elif isinstance(obj, MaterialSpec):
                assert obj.template in derefs, "Template wasn't in batch"
                assert obj.process in derefs, "Process wasn't in batch"
                for x in obj.properties:
                    assert x.property.template in derefs, "Referenced property wasn't in batch"
                    for y in x.conditions:
                        assert y.template in derefs, "Referenced condition wasn't in batch"
            elif isinstance(obj, MaterialRun):
                assert obj.spec in derefs, "Spec wasn't in batch"
                assert obj.process in derefs, "Process wasn't in batch"
            elif isinstance(obj, IngredientSpec):
                assert obj.process in derefs, "Process wasn't in batch"
                assert obj.material in derefs, "Material wasn't in batch"
            elif isinstance(obj, IngredientRun):
                assert obj.spec in derefs, "Spec wasn't in batch"
                assert obj.process in derefs, "Process wasn't in batch"
                assert obj.material in derefs, "Material wasn't in batch"
            elif isinstance(obj, MeasurementSpec):
                assert obj.template in derefs, "Template wasn't in batch"
                for x in obj.parameters:
                    assert x.template in derefs, "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert x.template in derefs, "Referenced condition wasn't in batch"
            elif isinstance(obj, MeasurementRun):
                assert obj.spec in derefs, "Spec wasn't in batch"
                assert obj.material in derefs, "Material wasn't in batch"
                for x in obj.parameters:
                    assert x.template in derefs, "Referenced parameter wasn't in batch"
                for x in obj.conditions:
                    assert x.template in derefs, "Referenced condition wasn't in batch"
                for x in obj.properties:
                    assert x.template in derefs, "Referenced property wasn't in batch"
            elif isinstance(obj, (PropertyTemplate, ConditionTemplate, ParameterTemplate)):
                pass  # These objects don't reference other objects
            else:
                pytest.fail(f"Unhandled type in batch: {type(obj)}")

    with pytest.raises(ValueError):
        batcher.batch(flatten(cake), batch_size=1)  # Errors out if impossible
