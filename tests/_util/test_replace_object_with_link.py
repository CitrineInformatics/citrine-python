"""Tests of the functions that replace objects with Links."""
from citrine._utils.functions import replace_objects_with_links


def test_simple_replacement():
    """A top-level object should turn into a link-by-uid."""
    json = dict(
        key='value',
        object=dict(
            type='material_run',
            uids={'my_id': '1', 'id': '17'}
        )
    )
    replaced_json = replace_objects_with_links(json)
    assert replaced_json == {'key': 'value',
                             'object': {'type': 'link_by_uid', 'scope': 'id', 'id': '17'}}


def test_nested_replacement():
    """A list of objects should turn into a list of link-by-uids."""
    json = dict(
        object=[dict(type='material_run', uids={'my_id': '1'}),
                dict(type='material_run', uids={'my_id': '2'})]
    )
    replaced_json = replace_objects_with_links(json)
    assert replaced_json == {'object': [{'type': 'link_by_uid', 'scope': 'my_id', 'id': '1'},
                                        {'type': 'link_by_uid', 'scope': 'my_id', 'id': '2'}]}


def test_failed_replacement():
    """An object that does not have a type and a uids dictionary should not be replaced."""
    json = dict(object=dict(
            some_field='material_run',
            uids={'my_id': '1', 'id': '17'}
        ))
    assert json == replace_objects_with_links(json)  # no type field

    json = dict(object=dict(
        type='material_run',
        uids='a uid string'
    ))
    assert json == replace_objects_with_links(json)  # uids is not a dictionary

    json = dict(object=dict(
        type='material_run',
        some_field={'my_id': '1', 'id': '17'}
    ))
    assert json == replace_objects_with_links(json)  # no uids field

    json = dict(object=dict(
        type='material_run',
        uids={}
    ))
    assert json == replace_objects_with_links(json)  # uids is an empty dictionary
