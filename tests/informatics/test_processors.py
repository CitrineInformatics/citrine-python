"""Tests for citrine.informatics.processors."""
import pytest

from citrine.informatics.processors import GridProcessor, EnumeratedProcessor


@pytest.fixture
def grid_processor() -> GridProcessor:
    """Build a GridProcessor for testing."""
    return GridProcessor('my thing', 'does a thing', dict(x=1))


@pytest.fixture
def enumerated_processor() -> EnumeratedProcessor:
    """Build an EnumeratedProcessor for testing."""
    return EnumeratedProcessor('my enumerated thing', 'enumerates the things', 10)


def test_grid_repr(grid_processor):
    assert str(grid_processor) == "<GridProcessor 'my thing'>"


def test_enumerated_repr(enumerated_processor):
    assert str(enumerated_processor) == "<EnumeratedProcessor 'my enumerated thing'>"


def test_grid_initialization(grid_processor):
    """Make sure the correct fields go to the correct places."""
    assert grid_processor.name == 'my thing'
    assert grid_processor.description == 'does a thing'
    assert grid_processor.grid_sizes == dict(x=1)


def test_enumerated_initialization(enumerated_processor):
    """Make sure the correct fields go to the correct places."""
    assert enumerated_processor.name == 'my enumerated thing'
    assert enumerated_processor.description == 'enumerates the things'
    assert enumerated_processor.max_size == 10
