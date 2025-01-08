from collections.abc import Callable
from types import UnionType
from typing import Generic, TypeVar, cast, get_args, get_type_hints

_TypeT = TypeVar("_TypeT", bound=type)
_T = TypeVar("_T")
_UNSET = object()


class _CachedClassProperty(Generic[_TypeT, _T]):
    """See [cached_class_property][]."""

    def __init__(self, getter: Callable[[_TypeT], _T]) -> None:
        self._getter = getter
        self._name: str | None = None

    def __get__(self, instance: None, owner: _TypeT) -> _T:
        if not self._name:
            return self._getter(owner)

        cached_value = owner.__dict__.get(self._name, _UNSET)
        if cached_value is _UNSET:
            value = self._getter(owner)
            setattr(owner, self._name, value)
            return value

        return cached_value

    def __set_name__(self, owner: _TypeT, name: str) -> None:
        self._name = name


def cached_class_property(getter: Callable[[_TypeT], _T]) -> _T:
    """Similar to [functools.cached_property][], but for class properties.

    Like [functools.cached_property][], the descriptor replaces itself with the computed value after the first lookup.
    """
    return cast(_T, _CachedClassProperty(getter))


def reify_type_hint(attr_name: str, bound: _TypeT) -> _TypeT:
    """Creates a [cached_class_property][] which returns the type hint of the given attribute."""
    return cached_class_property(lambda cls: get_mro_type_hint(cls, attr_name, bound))


def get_mro_type_hint(klass: type, attr_name: str, bound: _TypeT) -> _TypeT:
    """Returns the first type hint in `klass`'s MRO for the attribute `attr_name` and checks that it subclasses `bound`.

    For unions (esp. nullable attributes), the union is checked for a member which subclasses `bound` and that is
    returned. If no such member exists, a `TypeError` is raised.

    Raises:
        TypeError: If `klass` and its superclasses don't declare an attribute named `attr_name` or if the found type
                   hint and its union members don't subclass `bound`.
    """
    for superclass in klass.mro():
        hints = get_type_hints(superclass)
        if attr_name in hints:
            hint = hints[attr_name]
            break
    else:
        msg = (
            f"'{klass.__name__}' and its superclasses don't define a '{attr_name}' attribute. Did you extend the "
            f"correct class?"
        )
        raise TypeError(msg)

    if isinstance(hint, UnionType):
        for arg in get_args(hint):
            if isinstance(arg, type) and issubclass(arg, bound):
                hint = arg
                break

    if not issubclass(hint, bound):
        msg = f"Expected '{klass.__name__}.{attr_name}' to be a subclass of '{bound.__name__}', but was " f"'{hint}'"
        raise TypeError(msg)
    return hint
