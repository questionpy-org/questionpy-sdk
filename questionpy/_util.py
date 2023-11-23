from typing import TypeVar, Union, Literal, get_origin, get_args

_T = TypeVar("_T")


def get_type_arg(derived: type, generic_base: type, arg_index: int, *,
                 bound: type = object, default: Union[_T, Literal["nodefault"]] = "nodefault") -> Union[type, _T]:
    """Finds a type arg used by `derived` when inheriting from `generic_base`.

    Args:
        derived: The type which directly inherits from `generic_base`.
        generic_base: One of the direct bases of `derived`.
        arg_index: Among the type arguments accepted by `generic_base`, this is the index of the type argument to
                   return.
        bound: Raises :class:`TypeError` if the type argument is not a subclass of this.
        default: Returns this when the type argument isn't given. If unset, an error is raised instead.

    Raises:
        TypeError: Upon any of the following:
            - `derived` is not a direct subclass of `generic_base` (transitive subclasses are not supported),
            - the type argument is not given and `default` is unset, or
            - the type argument is not a subclass of `bound`
    """
    # __orig_bases__ is only present when at least one base is a parametrized generic.
    # See PEP 560 https://peps.python.org/pep-0560/
    if "__orig_bases__" in derived.__dict__:
        bases = derived.__dict__["__orig_bases__"]
    else:
        bases = derived.__bases__

    for base in bases:
        origin = get_origin(base) or base
        if origin is generic_base:
            args = get_args(base)
            if not args or arg_index >= len(args):
                # No type argument provided.
                if default == "nodefault":
                    raise TypeError(f"Missing type argument on {generic_base.__name__} (type arg #{arg_index})")

                return default

            arg = args[arg_index]
            if not isinstance(arg, type) or not issubclass(arg, bound):
                raise TypeError(f"Type parameter '{arg!r}' of {generic_base.__name__} is not a subclass of "
                                f"{bound.__name__}")
            return arg

    raise TypeError(f"{derived.__name__} is not a direct subclass of {generic_base.__name__}")
