from collections.abc import Callable
from types import UnionType
from typing import TYPE_CHECKING, cast, get_args, get_type_hints

from questionpy_common.environment import Package, PackageNamespaceAndShortName, get_qpy_environment

if TYPE_CHECKING:
    from questionpy import Attempt

_UNSET = object()


class _CachedClassProperty[ReceiverT: type, ValueT]:
    """See [cached_class_property][]."""

    def __init__(self, getter: Callable[[ReceiverT], ValueT]) -> None:
        self._getter = getter
        self._name: str | None = None

    def __get__(self, instance: None, owner: ReceiverT) -> ValueT:
        if not self._name:
            # __set_name__ wasn't called. The property is probably not defined in the class body, or wrapped by
            # something.
            return self._getter(owner)

        # Subsequent lookups _should_ bypass the property entirely, but if for some reason they don't, we check the
        # class dict explicitly.
        cached_value = owner.__dict__.get(self._name, _UNSET)
        if cached_value is _UNSET:
            value = self._getter(owner)
            # By setting an attribute on the class, future lookups should bypass the property entirely.
            setattr(owner, self._name, value)
            return value

        return cached_value

    def __set_name__(self, owner: ReceiverT, name: str) -> None:
        self._name = name


def cached_class_property[ReceiverT: type, ValueT](getter: Callable[[ReceiverT], ValueT]) -> ValueT:
    """Similar to [functools.cached_property][], but for class properties.

    Like [functools.cached_property][], the descriptor replaces itself with the computed value after the first lookup.
    """
    return cast("ValueT", _CachedClassProperty(getter))


def reify_type_hint[ReceiverT: type](attr_name: str, bound: ReceiverT) -> ReceiverT:
    """Creates a [cached_class_property][] which returns the type hint of the given attribute."""
    return cached_class_property(lambda cls: get_mro_type_hint(cls, attr_name, bound))


def get_mro_type_hint[BoundT: type](klass: type, attr_name: str, bound: BoundT) -> BoundT:
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
        msg = f"Expected '{klass.__name__}.{attr_name}' to be a subclass of '{bound.__name__}', but was '{hint}'"
        raise TypeError(msg)
    return hint


def get_package_by_python_module(module_name: str) -> Package:
    """Returns the package which the given Python module is a part of."""
    try:
        namespace, short_name, *_ = module_name.split(".", maxsplit=2)
        env = get_qpy_environment()
        key = PackageNamespaceAndShortName(namespace=namespace, short_name=short_name)
        return env.packages[key]
    except (KeyError, ValueError) as e:
        msg = (
            f"Current package namespace and short name could not be determined from module name '{module_name}'. "
            f"Please do not modify the '__module__' or '__package__' attributes."
        )
        raise ValueError(msg) from e


def get_package_by_attempt(attempt: "Attempt") -> Package:
    """Returns the package in which the attempt was defined."""
    return get_package_by_python_module(attempt.__module__)
