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
    def bimap(self, f: Callable[[A], C], g: Callable[[B], D]) -> "Either[C, D]":
        if isinstance(self, Left):
            return Left(f(self.value()))
        else:
            return Right(g(self.value()))

    """Left projection of Either type."""
    def left(self) -> A:
        if isinstance(self, Left):
            return self.value()
        else:
            return None

    """Right projection of Either type."""
    def right(self) -> B:
        if isinstance(self, Right):
            return self.value()
        else:
            return None

    def value(self) -> Union[A, B]:
        raise NotImplementedError


class Left(Either[A, B]):
    def __init__(self, value: Union[A,B]):
        self._value = value

    def value(self) -> A:
        return self._value

class Right(Either[A, B]):
    def __init__(self, value: Union[A,B]):
        self._value = value

    def value(self) -> B:
        return self._value
