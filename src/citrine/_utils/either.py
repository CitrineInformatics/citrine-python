from abc import abstractmethod
from typing import Callable, Generic, TypeVar, Union

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


class Either(Generic[A, B]):
    """A type that can be either of two types."""

    @abstractmethod
    def __init__(self, value: Union[A,B]):
        raise NotImplementedError

    """
    Bi-functor implementation for Either type.

    Parameters:
    -----------
    f: Callable[[A], C]
        Function to apply to the left value.
    g: Callable[[B], D]
        Function to apply to the right value.

    """
    def bimap(this, f: Callable[[A], C], g: Callable[[B], D]) -> "Either[C, D]":
        if (isinstance(this, Left)):
            return Left(f(this.value()))
        else:
            return Right(g(this.value()))

    """Left projection of Either type."""
    def left(this) -> A:
        if (isinstance(this, Left)):
            return this.value()
        else:
            return None

    """Right projection of Either type."""
    def right(this) -> B:
        if (isinstance(this, Right)):
            return this.value()
        else:
            return None

class Left(Either[A, B]):
    def __init__(self, value: Union[A,B]):
        self._value = value

class Right(Either[A, B]):
    def __init__(self, value: Union[A,B]):
        self._value = value
