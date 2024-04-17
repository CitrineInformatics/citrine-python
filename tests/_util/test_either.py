import pytest
from citrine._utils.either import Either, Left, Right

def test_initialization():
    """
    The Either class is an abstract class, so it should raise a NotImplementedError when trying to initialize it.
    """
    with pytest.raises(NotImplementedError):
        Either(1)

def test_left():
    """
    Test that the left projection works as expected.
    """
    my_value = Left(1)
    assert isinstance(my_value, Left)
    assert my_value.left() == 1
    assert my_value.right() == None

def test_right():
    """
    Test that the right projection works as expected.
    """
    my_value = Right("hola")
    assert isinstance(my_value, Right)
    assert my_value.value() == "hola"
    assert my_value.left() == None

def test_bimap():
    """
    Testing that the bifunctor maps both values correctly.
    """
    my_value = Right("String")
    my_other_value = Left(1)
    f = lambda x: x+1
    g = lambda x: "Some" + x
    assert my_value.bimap(f, g).value() == "SomeString"
    assert my_other_value.bimap(f, g).value() == 2

def test_bifunctor():
    """
    Testing that the bifunctor follows functor laws.
    """
    my_value = Right("String")
    my_other_value = Left(1)

    """Identity - both sides"""
    assert my_value.bimap(lambda x: x, lambda x: x).value() == my_value.value()
    assert (
        my_other_value.bimap(lambda x: x, lambda x: x).value()
        == my_other_value.value()
    )

    """Composition of functions - both sides"""
    f1 = lambda x: x + 1
    f2 = lambda x: x * 2
    g1 = lambda x: "Some" + x
    g2 = lambda x: x + "Concatenated"

    assert my_value.bimap(f1, g1).bimap(f2, g2).value() == my_value.bimap(lambda x: f2(f1(x)), lambda x: g2(g1(x))).value()
    assert (
        my_other_value.bimap(f1, g1).bimap(f2, g2).value()
        == my_other_value.bimap(lambda x: f2(f1(x)), lambda x: g2(g1(x))).value()
    )
