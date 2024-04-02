from types import UnionType
from typing import TypeVar, get_args, get_type_hints

_T = TypeVar("_T", bound=type)


def get_mro_type_hint(klass: type, attr_name: str, bound: _T) -> _T:
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
