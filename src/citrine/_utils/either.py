from abc import abstractmethod
from typing import Callable, Generic, TypeVar, Union

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


class Either(Generic[A, B]):
    """A type that can be either of two types."""

    @abstractmethod
    def __init__(self, value: Union[A, B]):
        raise NotImplementedError

    def bimap(self, f: Callable[[A], C], g: Callable[[B], D]) -> "Either[C, D]":
        """
        Bi-functor implementation for Either type.

         Parameters:
        -----------
        f: Callable[[A], C]
            Function to apply to the left value.
        g: Callable[[B], D]
            Function to apply to the right value.
        """
        if isinstance(self, Left):
            return Left(f(self.value()))
        else:
            return Right(g(self.value()))

    def left(self) -> A:
        """Left projection of Either type."""
        if isinstance(self, Left):
            return self.value()
        else:
            return None

    def right(self) -> B:
        """Right projection of Either type."""
        if isinstance(self, Right):
            return self.value()
        else:
            return None


class Left(Either[A, B]):
    """Left side component of the Either sum type."""

    def __init__(self, value: Union[A, B]):
        self._value = value

    def value(self) -> A:
        """Return the value of the Left component."""
        return self._value


class Right(Either[A, B]):
    """Right side component of the Either sum type."""

    def __init__(self, value: Union[A, B]):
        self._value = value

    def value(self) -> B:
        """Return the value of the Right component."""
        return self._value
