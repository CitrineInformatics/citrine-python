import uuid

import pytest
from mock import patch, call, MagicMock, mock_open
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.link_by_uid import LinkByUID

from citrine._utils.functions import get_object_id, validate_type, object_to_link_by_uid, \
    rewrite_s3_links_locally, write_file_locally, shadow_classes_in_module
from gemd.entity.attribute.property import Property
from citrine.resources.condition_template import ConditionTemplate


def test_get_object_id_from_base_attribute():
    with pytest.raises(ValueError):
        get_object_id(Property('some property'))


def test_get_object_id_from_data_concepts():
    uid = str(uuid.uuid4())
    template = ConditionTemplate(
        name='test',
        bounds=RealBounds(0.0, 1.0, ''),
        uids={'id': uid}
    )
    assert uid == get_object_id(template)


def test_get_object_id_from_data_concepts_id_is_none():
    template = ConditionTemplate(
        name='test',
        bounds=RealBounds(0.0, 1.0, '')
    )

    with pytest.raises(ValueError):
        template.uids = {'id': None}


def test_get_object_id_link_by_uid_bad_scope():
    with pytest.raises(ValueError):
        get_object_id(LinkByUID('bad_scope', '123'))


def test_get_object_id_wrong_type():
    with pytest.raises(TypeError):
        get_object_id('no id here')


def test_validate_type_wrong_type():
    with pytest.raises(Exception):
        validate_type({'type': 'int'}, 'foo')


def test_validate_type_set_type():
    assert {'type': 'int'} == validate_type({}, 'int')


def test_object_to_link_by_uid_missing_uids():
    assert {'foo': 'bar'} == object_to_link_by_uid({'foo': 'bar'})


def test_rewrite_s3_links_locally():
    assert "http://localhost:9572" == rewrite_s3_links_locally("http://localstack:4572")


@patch("os.path.isdir")
@patch("os.path.join")
@patch("os.makedirs")
def test_write_file_locally(mock_makedirs, mock_join, mock_isdir):
    mock_isdir.return_value = False
    mock_join.return_value = "/User/is/fake/myfile.pdf"
    with patch("builtins.open", mock_open()) as m:
        write_file_locally(b"something", "/User/is/fake/myfile.pdf")
        assert m.call_args_list == [call('/User/is/fake/myfile.pdf', 'wb')]
        handle = m()
        handle.write.assert_called_once_with(b'something')
    mock_makedirs.assert_called_once_with("/User/is/fake")


def test_write_file_locally_fails_with_no_filename():
    with pytest.raises(ValueError):
        write_file_locally(b"anything", "/user/is/")


def test_shadow_classes_in_module():

    # Given
    from tests._util import source_mod, target_mod
    assert getattr(target_mod, 'ExampleClass', None) == None

    # When
    shadow_classes_in_module(source_mod, target_mod)

    # Then (ensure the class is copied over)
    copied_class = getattr(target_mod, 'ExampleClass', None) # Do this vs a direct ref so IJ doesn't warn us
    assert copied_class == source_mod.ExampleClass

    # Python also considers the classes equivalent
    assert issubclass(copied_class, source_mod.ExampleClass)
    assert issubclass(source_mod.ExampleClass, copied_class)
