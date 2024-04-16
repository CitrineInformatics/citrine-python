from citrine._utils.either import Left, Right

def test_left():
    my_value = Left(1)
    assert isinstance(my_value, Left)
    assert my_value.value() == 1

def test_right():
    my_value = Right("hola")
    assert isinstance(my_value, Right)
    assert my_value.value() == "hola"

def test_bimap():
    my_value = Right("String")
    my_other_value = Left(1)
    f = lambda x: x+1
    g = lambda x: "Some" + x
    assert my_value.bimap(f, g).value() == "SomeString"
    assert my_other_value.bimap(f, g).value() == 2