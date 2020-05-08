"""Test the Paginator"""
from mock import Mock

from citrine._rest.paginator import Paginator


def test_validate_mock_fetcher():
    """Just ensure our mock fetcher method does the right thing for what the paginator expects"""
    mock_fetcher = mocked_fetcher("a", "b")

    # Make calls (and ignore arguments on the callable), and ensure we get back the above elements, each wrapped in a
    # list, and the final call should be an empty list.
    assert mock_fetcher("a", "b") == (["a"], "next_uri")
    assert mock_fetcher() == (["b"], "next_uri")
    assert mock_fetcher() == ([], "")


def test_paginator_fetches_single_page():
    # Return a single page with 2 elements
    result = Paginator().paginate(mocked_fetcher(["a", "b"]), lambda x: x, per_page=2)
    assert list(result) == ["a", "b"]


def test_pagination_across_two_pages():
    result = Paginator().paginate(mocked_fetcher("a", "b"), lambda x: x, per_page=1)
    assert list(result) == ["a", "b"]


def test_pagination_stops_when_initial_item_repeated():
    result = Paginator().paginate(mocked_fetcher("a", "b", "a"), lambda x: x, per_page=1)
    assert list(result) == ["a", "b"]


def mocked_fetcher(*args):
    """
    Take a list of arguments, and return them (wrapped in a list) in subsequent calls to this mock.
    Finish with an empty list.

    This lets us mock a fetcher easily.
    """
    mock_fetcher = Mock()
    args_in_lists = [list(a) for a in args]
    args_in_lists = [(a, "next_uri") for a in args_in_lists]
    args_in_lists.append(([], ""))
    mock_fetcher.side_effect = list(args_in_lists)
    return mock_fetcher
