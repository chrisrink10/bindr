import sys
import re
from typing import (
    TypeVar,
    NamedTuple,
    Type,
    List,
    Iterable,
    MutableMapping,
    Mapping,
    Dict,
    Set,
    Any,
    Tuple,
    Optional,
    Union,
)


C = TypeVar("C")
Fields = Dict[str, Type]


class _ConcreteClassDetails(NamedTuple):
    type_: Type
    nargs: int


def _get_named_tuple_fields(cls: Type[C]) -> Fields:
    """Return a dict of field names to types."""
    assert _is_named_tuple(cls), "Class must be created via NamedTuple"
    return cls._field_types  # type: ignore # pylint: disable=protected-access


if sys.version_info >= (3, 7):

    import dataclasses  # pylint: disable=import-error

    def _get_concrete_type(field_type) -> _ConcreteClassDetails:
        return _ConcreteClassDetails(field_type.__origin__, len(field_type.__args__))

    def _get_fields(cls) -> Fields:
        try:
            return {field.name: field.type for field in dataclasses.fields(cls)}
        except TypeError:
            return _get_named_tuple_fields(cls)


elif sys.version_info >= (3, 6):
    _ALLOWED_GENERICS: Dict[Type, _ConcreteClassDetails] = {
        List: _ConcreteClassDetails(list, 1),
        Iterable: _ConcreteClassDetails(list, 1),
        MutableMapping: _ConcreteClassDetails(dict, 2),
        Mapping: _ConcreteClassDetails(dict, 2),
        Dict: _ConcreteClassDetails(dict, 2),
        Set: _ConcreteClassDetails(set, 1),
    }

    def _get_concrete_type(field_type) -> _ConcreteClassDetails:
        concrete_type_details: Optional[_ConcreteClassDetails] = _ALLOWED_GENERICS.get(
            field_type.__origin__, None
        )
        if concrete_type_details is None:
            raise TypeError(f"Generic type must be one of: {_ALLOWED_GENERICS.keys()}")
        return concrete_type_details

    _get_fields = _get_named_tuple_fields


assert sys.version_info >= (3, 6), "Bindr does not work with Python versions <= 3.5"


def _is_named_tuple(concrete_type: Type[C]) -> bool:
    """Return True if concrete_type is a type generated from a named tuple."""
    return issubclass(concrete_type, tuple) and hasattr(concrete_type, "_field_types")


def _is_generic(cls) -> bool:
    """Return True if cls is a generic type. For example, List or List[int]."""
    if cls.__module__ != "typing":
        if not any(c.__module__ == "typing" for c in cls.mro()):
            return False

    params = getattr(cls, "__parameters__", ())
    if params:
        return True

    return bool(getattr(cls, "__args__", ()))


def _is_base_generic(cls) -> bool:
    """Return True if cls is a generic without specified parameters. For example
    List, but not List[int]."""
    return _is_generic(cls) and bool(cls.__parameters__)


def _is_specialized_generic(cls) -> bool:
    """Return True if cls is a generics with arguments. For example, List[int], but
    not List."""
    return _is_generic(cls) and not cls.__parameters__


def _is_optional(cls) -> bool:
    """Return true if cls is specialized Optional."""
    return (
        _is_specialized_generic(cls)
        and cls.__origin__ is Union
        and len(cls.__args__) == 2
        and type(None) in cls.__args__  # noqa
    )


def _coerce_type(
    concrete_type: Type[C], val: Any, raise_if_missing_attr: bool = True
) -> C:
    """Coerce a value to the concrete type given, binding attributes in a named tuple class
    if concrete type is a named tuple."""
    if issubclass(
        concrete_type, (bytes, complex, dict, float, frozenset, int, list, set, str)
    ):
        return concrete_type(val)  # type: ignore
    elif issubclass(concrete_type, tuple) and not _is_named_tuple(concrete_type):
        return concrete_type(val)  # type: ignore
    else:
        return bind(concrete_type, val, raise_if_missing_attr=raise_if_missing_attr)


def _coerce_generic_type(  # pylint: disable=inconsistent-return-statements
    field_type: Type, val: Any, raise_if_missing_attr: bool = True
) -> Tuple[Type, Any]:
    """Coerce a generic type into a concrete type."""
    assert _is_specialized_generic(field_type), "Cannot coerce a non-generic type"

    type_args = field_type.__args__
    concrete_type_details = _get_concrete_type(field_type)

    assert concrete_type_details.nargs == len(
        type_args
    ), "Number of type arguments must match expected"

    field_type = concrete_type_details.type_

    if issubclass(field_type, dict):
        return (
            field_type,
            {
                _coerce_type(
                    type_args[0], k, raise_if_missing_attr=raise_if_missing_attr
                ): _coerce_type(
                    type_args[1], v, raise_if_missing_attr=raise_if_missing_attr
                )
                for k, v in val.items()
            },
        )
    elif issubclass(field_type, (list, frozenset, set, tuple)):
        return (
            field_type,
            field_type(
                _coerce_type(
                    type_args[0], e, raise_if_missing_attr=raise_if_missing_attr
                )
                for e in val
            ),
        )

    assert False, "Generic type must have been handled"


def _coerce_optional(
    field_type: Type[C], val: Any, raise_if_missing_attr: bool = True
) -> Optional[C]:
    """Coerce an optional typed value to """
    if val is None:
        return None
    type_args = tuple(
        filter(
            lambda t: t is not type(None), field_type.__args__  # type: ignore # noqa
        )
    )
    assert len(type_args) == 1, "Optional types can only have two type arguments"
    return _coerce_type(type_args[0], val, raise_if_missing_attr=raise_if_missing_attr)


_MUNGE_NAMES = re.compile(r"[\s|-]")


def bind(cls: Type[C], dct: dict, raise_if_missing_attr: bool = True) -> C:
    """Recursively bind dictionary values to attributes on NamedTuple instances whose
    name matches dictionary keys."""
    field_types = _get_fields(cls)
    final_fields = {}
    for key, val in dct.items():
        key = re.sub(_MUNGE_NAMES, "_", key)
        field_type = field_types.get(key, None)
        if field_type is None:
            if raise_if_missing_attr:
                raise AttributeError(f"Class {cls} does not have attribute {key}")
            continue

        if _is_base_generic(field_type):
            raise TypeError(
                f"Must use specialized generic for field type, not {field_type}"
            )
        elif _is_optional(field_type):
            final_fields[key] = _coerce_optional(
                field_type, val, raise_if_missing_attr=raise_if_missing_attr
            )
            continue
        elif _is_specialized_generic(field_type):
            field_type, val = _coerce_generic_type(
                field_type, val, raise_if_missing_attr=raise_if_missing_attr
            )

        final_fields[key] = _coerce_type(
            field_type, val, raise_if_missing_attr=raise_if_missing_attr
        )

    return cls(**final_fields)  # type: ignore
