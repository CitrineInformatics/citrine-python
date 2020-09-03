"""Test the Paginator"""
from uuid import uuid4

from mock import Mock

from citrine._rest.paginator import Paginator


def test_validate_mock_fetcher():
    """Just ensure our mock fetcher method does the right thing for what the paginator expects"""
    mock_fetcher = mocked_fetcher(DummyResource("a"), DummyResource("b"))

    # Make calls (and ignore arguments on the callable), and ensure we get back the above elements, each wrapped in a
    # list, and the final call should be an empty list.
    assert mock_fetcher(DummyResource("a"), DummyResource("b")) == ([DummyResource("a")], "next_uri")
    assert mock_fetcher() == ([DummyResource("b")], "next_uri")
    assert mock_fetcher() == ([], "")


def test_pagination_across_two_pages():
    result = Paginator().paginate(mocked_fetcher(DummyResource("a"), DummyResource("b")), lambda x: x, per_page=1)
    assert list(result) == [DummyResource("a"), DummyResource("b")]


def test_pagination_stops_when_initial_item_repeated():
    a = DummyResource("a")
    result = Paginator().paginate(mocked_fetcher(a, DummyResource("b"), a), lambda x: x, per_page=1)
    assert list(result) == [a, DummyResource("b")]


def test_pagination_deduplicates_repeated_intermediate_values():
    a = DummyResource("a")
    b = DummyResource("b")
    c = DummyResource("c")
    result = Paginator().paginate(mocked_fetcher(a, b, b, b, b, b, b, c, c), lambda x: x, per_page=1)
    assert list(result) == [a, b, c]


def mocked_fetcher(*args):
    """
    Take a list of arguments, and return them (wrapped in a list) in subsequent calls to this mock.
    Finish with an empty list.

    This lets us mock a fetcher easily.
    """
    mock_fetcher = Mock()
    args_in_lists = [[a] for a in args]
    args_in_lists = [(a, "next_uri") for a in args_in_lists]
    args_in_lists.append(([], ""))
    mock_fetcher.side_effect = list(args_in_lists)
    return mock_fetcher


class DummyResource(object):
    """
    Dummy resource that stores a string val
    """

    def __init__(self, val: str):
        self.val = val
        self.uid = uuid4()

    def __eq__(self, other):
        return self.val == other.val
