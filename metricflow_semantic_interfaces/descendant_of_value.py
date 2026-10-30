from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from metricflow_semantic_interfaces.errors import InvalidQuerySyntax


def _string_literal(value: str) -> str:
    if "'" in value or "\\" in value:
        raise InvalidQuerySyntax(
            f"descendant_of does not accept a string with a single quote or a backslash: {value!r}"
        )
    return f"'{value}'"


_LITERAL_BY_VALUE_TYPE: Mapping[type, Callable[[str], str]] = {int: str, str: _string_literal}


@dataclass(frozen=True)
class DescendantOfValue:
    """The value passed to `descendant_of(...)`, as a literal that can be written into SQL as is.

    The value is placed in the SQL text instead of being passed as a bind parameter, and quote escaping differs between
    SQL engines, so strings with a single quote or a backslash are rejected.
    """

    # e.g. `'e1'` for the string e1, or `7` for the integer 7.
    sql: str

    @staticmethod
    def create(value: object) -> DescendantOfValue:
        """Create from a string or an integer. Other types, including bool, are rejected."""
        literal = _LITERAL_BY_VALUE_TYPE.get(type(value))
        if literal is None:
            raise InvalidQuerySyntax(f"descendant_of takes a string or an integer, but got {value!r}")
        return DescendantOfValue(sql=literal(value))  # type: ignore[arg-type]
