"""Tests for citrine.informatics.processors serialization."""
import pytest

from citrine.informatics.processors import Processor, GridProcessor, EnumeratedProcessor, \
    MonteCarloProcessor


@pytest.fixture(params=[
    MonteCarloProcessor("test", "mc optimizer test"),
    EnumeratedProcessor("test", "test_enumeration", max_size=64),
    GridProcessor("test", "test_grid", grid_sizes={"foo": 2, "bar": 5})
])
def processor(request):
    return request.param


def test_deser_from_parent(processor):
    # Serialize and deserialize the processor, making sure they are round-trip serializable
    data = processor.dump()
    data.update({"status": "READY"})
    deserialized = Processor.build(data)
    assert processor == deserialized
    "{} passed!".format(processor)  # check str method


def test_invalid_eq(processor):
    other = None
    assert not processor == other
