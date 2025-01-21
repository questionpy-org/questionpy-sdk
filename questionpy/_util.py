from types import UnionType
from typing import TYPE_CHECKING, TypeVar, get_args, get_type_hints

from questionpy_common.environment import Package, PackageNamespaceAndShortName, get_qpy_environment

if TYPE_CHECKING:
    from questionpy import Attempt

_T = TypeVar("_T", bound=type)


def get_mro_type_hint(klass: type, attr_name: str, bound: _T) -> _T:
    # FIXME: This function is called too early, when the classes referenced in forward refs may not be defined yet.
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


def get_package_by_attempt(attempt: "Attempt") -> Package:
    """Returns the package in which the attempt was defined."""
    try:
        namespace, short_name, *_ = attempt.__module__.split(".", maxsplit=2)
        env = get_qpy_environment()
        key = PackageNamespaceAndShortName(namespace=namespace, short_name=short_name)
        return env.packages[key]
    except (KeyError, ValueError) as e:
        msg = (
            "Current package namespace and shortname could not be determined from '__module__' attribute. Please do "
            "not modify the '__module__' attribute."
        )
        raise ValueError(msg) from e
