"""Tests of the method that removes None values from object dictionaries."""
from citrine._utils.functions import scrub_none


def test_scrub_none():
    """Test that scrub_none() when applied to some examples yields expected results."""
    json = dict(
        key1=1,
        key2=None
    )
    scrub_none(json)
    assert json == dict(key1=1)

    json = dict(
        key1=dict(
            key11='foo',
            key12=None
        ),
        key2=[
            dict(key21=None, key22=17),
            dict(key23=None),
            dict(key24=34, key25=51)
        ]
    )
    scrub_none(json)
    assert json == dict(
        key1=dict(key11='foo'),
        key2=[dict(key22=17), dict(), dict(key24=34, key25=51)]
    )

    json = dict(
        key1=1,
        key2=[None, 'foo', None, None, 'bar', None],
        key3=[None, None, None]
    )
    scrub_none(json)
    # None should not be removed from lists
    assert json == dict(
        key1=1,
        key2=[None, 'foo', None, None, 'bar', None],
        key3=[None, None, None]
    )
