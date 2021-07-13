"""Tests for citrine.informatics.processors."""
import pytest

from citrine.informatics.processors import GridProcessor, EnumeratedProcessor


@pytest.fixture
def grid_processor() -> GridProcessor:
    """Build a GridProcessor for testing."""
    return GridProcessor('my thing', description='does a thing', grid_sizes=dict(x=1))


@pytest.fixture
def enumerated_processor() -> EnumeratedProcessor:
    """Build an EnumeratedProcessor for testing."""
    return EnumeratedProcessor('my enumerated thing', description='enumerates the things', max_candidates=10)


def test_grid_initialization(grid_processor):
    """Make sure the correct fields go to the correct places."""
    assert grid_processor.name == 'my thing'
    assert grid_processor.description == 'does a thing'
    assert grid_processor.grid_sizes == dict(x=1)


def test_enumerated_initialization(enumerated_processor):
    """Make sure the correct fields go to the correct places."""
    assert enumerated_processor.name == 'my enumerated thing'
    assert enumerated_processor.description == 'enumerates the things'
    assert enumerated_processor.max_candidates == 10


def test_enumerated_defaults():
    """Make sure deprecated arguments and defaults work as expected."""
    assert EnumeratedProcessor("f", description="b").max_candidates == 1000
    assert EnumeratedProcessor("f", description="b", max_candidates=12).max_candidates == 12
