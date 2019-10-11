import uuid

import pytest
from mock import patch, call, MagicMock, mock_open
from taurus.entity.bounds.real_bounds import RealBounds
from taurus.entity.link_by_uid import LinkByUID

from citrine._utils.functions import set_default_uid, get_object_id, validate_type, object_to_link_by_uid, \
    rewrite_s3_links_locally, write_file_locally
from citrine.attributes.property import Property
from citrine.resources.condition_template import ConditionTemplate


def test_set_default_id_non_uuid():
    with pytest.raises(ValueError):
        set_default_uid({'id': 'not-valid'})


def test_set_default_id_non_dict():
    with pytest.raises(Exception):
        set_default_uid('not a dict')


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
    template.uids = {'id': None}

    with pytest.raises(ValueError):
        get_object_id(template)


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
    mock_join.return_value = "/User/is/fake/myfile.pdf"
    with patch('os.path.split') as mock_split:

        with patch("builtins.open", mock_open()) as m:
            mock_split.return_value = ("/User/is/fake", "myfile.pdf")
            write_file_locally(b"something", "/User/is/fake/myfile.pdf")
            assert m.call_args_list == [call('/User/is/fake/myfile.pdf', 'wb')]
            handle = m()
            handle.write.assert_called_once_with(b'something')


def test_write_file_locally_fails_with_no_filename():
    with pytest.raises(ValueError):
        write_file_locally(b"anything", "/user/is/")
