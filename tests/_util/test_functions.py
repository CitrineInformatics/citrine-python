from pathlib import Path
import pytest
import uuid

from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.link_by_uid import LinkByUID

from citrine._utils.functions import get_object_id, validate_type, object_to_link_by_uid, \
    rewrite_s3_links_locally, write_file_locally, shadow_classes_in_module, migrate_deprecated_argument, \
    format_escaped_url, MigratedClassMeta, generate_shared_meta
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
    assert "http://localhost:9566" == rewrite_s3_links_locally("http://localstack:4566", "http://localhost:9566")


def test_write_file_locally(tmpdir):
    target = Path(tmpdir) / "user/is/fake/myfile.pdf"
    assert not target.parent.is_dir()
    assert not target.exists()
    write_file_locally(b"something", target)
    assert target.exists()
    assert target.read_text() == "something"

    write_file_locally(b"something else", str(target))
    assert target.read_text() == "something else"


def test_write_file_locally_fails_with_no_filename():
    with pytest.raises(ValueError):
        write_file_locally(b"anything", "/user/is/")


def test_write_file_locally_fails_if_directory(tmpdir):
    newdir = Path(tmpdir) / "wasnt/there/before"
    newdir.mkdir(parents=True)
    with pytest.raises(ValueError):
        write_file_locally(b"anything", newdir)


def test_migrated_class():
    """
    Test that inheritance and instantiation of a migrated class warn.

    Note we use `Property` because it has the higher level of difficulty of because
    it has a custom metaclass.

    """
    # Declaring the migrated class raises no concern
    with pytest.warns(None) as w:
        class MigratedProperty(Property,
                               deprecated_in="1.2.3",
                               removed_in="2.0.0",
                               metaclass=generate_shared_meta(Property)):
            pass
    assert len(w.list) == 0

    with pytest.deprecated_call():
        MigratedProperty(name="I'm a property!")

    with pytest.deprecated_call():
        class DerivedProperty(MigratedProperty):
            pass

    assert len(w.list) == 0  # Deriving from a derived class is fine
    with pytest.warns(None) as w:
        class DoublyDerivedProperty(DerivedProperty):
            pass

    assert len(w.list) == 0  # Deriving from a derived class is fine

    class IndependentProperty(Property):
        pass

    assert issubclass(MigratedProperty, Property)
    assert issubclass(Property, MigratedProperty)
    assert issubclass(DerivedProperty, MigratedProperty)
    assert issubclass(DoublyDerivedProperty, MigratedProperty)
    assert issubclass(IndependentProperty, MigratedProperty)
    assert isinstance(Property("Property Name"), MigratedProperty)

    with pytest.raises(TypeError, match="deprecated_in"):
        class NoVersionInfo(Property, metaclass=generate_shared_meta(Property)):
            pass

    with pytest.raises(TypeError, match="precisely"):
        class NoParent(deprecated_in="1.2.3",
                       removed_in="2.0.0",
                       metaclass=MigratedClassMeta):
            pass

    assert generate_shared_meta(dict) is MigratedClassMeta


def test_recursive_subtype_recovery():
    """
    ABC + MigratedClassMeta creates an infinite loop of type checks for a reason
    I do not grasp.  This is a minimal replication for why there's a try-except
    in MigratedClassMeta.__subclasscheck__.

    """
    import abc

    class Simple(abc.ABC):
        pass

    class MigratedProperty(Simple,
                           deprecated_in="1.2.3",
                           removed_in="2.0.0",
                           metaclass=MigratedClassMeta):
        pass

    assert not issubclass(dict, Simple)


def test_shadow_classes_in_module():

    # Given
    from tests._util import source_mod, target_mod
    assert getattr(target_mod, 'ExampleClass', None) == None

    # When
    with pytest.deprecated_call():
        shadow_classes_in_module(source_mod, target_mod)

    # Then (ensure the class is copied over)
    copied_class = getattr(target_mod, 'ExampleClass', None) # Do this vs a direct ref so IJ doesn't warn us
    assert copied_class == source_mod.ExampleClass

    # Python also considers the classes equivalent
    assert issubclass(copied_class, source_mod.ExampleClass)
    assert issubclass(source_mod.ExampleClass, copied_class)

    # Reset target_mod status
    for attr in dir(target_mod):
        delattr(target_mod, attr)


def test_migrate_deprecated_argument():
    with pytest.raises(ValueError):
        # ValueError if neither argument is specified
        migrate_deprecated_argument(None, "new name", None, "old name")

    with pytest.warns(DeprecationWarning):
        with pytest.raises(ValueError):
            # ValueError if both arguments are specified
            migrate_deprecated_argument("something", "new name", "something else", "old name")

    # Return the value if the new argument is specified
    assert migrate_deprecated_argument(14, "new name", None, "old name") == 14

    with pytest.warns(DeprecationWarning) as caught:
        # If the old argument is specified, return the value and throw a deprecation warning
        assert migrate_deprecated_argument(None, "new name", 15, "old name") == 15
        msg = str(caught[0].message)
        assert "old name" in msg and "new name" in msg


def test_format_escaped_url():
    url = format_escaped_url('http://base.com/{}/{}/{word1}/{word2}', 1, '&', word1='fine', word2='+/?#')
    assert 'http://base.com/' in url
    assert 'fine' in url
    assert '1' in url
    for c in '&' + '+?#':
        assert c not in url
    assert 6 == sum(c == '/' for c in url)
