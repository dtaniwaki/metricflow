from __future__ import annotations

from dataclasses import dataclass

from metricflow_semantic_interfaces.dataclass_serialization import SerializableDataclass

_CTE_NAME = "descendant_of_tree"
_CTE_COLUMN_NAME = "descendant_of_value"


@dataclass(frozen=True)
class DescendantOfSource(SerializableDataclass):
    """Where the key and the parent of a self-referencing hierarchy level are read from."""

    # The table that has one row per member of the hierarchy, e.g. `some_schema.dim_employees`.
    relation_sql: str
    # The SQL expression for the value of the level in a row, e.g. `employee_id`.
    key_expr: str
    # The SQL expression for the parent of that value in the row, e.g. `manager_id`.
    parent_expr: str


def render_descendant_of_sql(column_name: str, source: DescendantOfSource, value_sql: str) -> str:
    """Return a condition that is true for the value and for every value below it in the hierarchy.

    The recursion starts from the rows whose parent is the value, so the value need not have a row of its own. The value
    itself is matched by the first condition. `UNION` (not `UNION ALL`) drops values that were already reached, so
    on DuckDB and Postgres parents that form a cycle end the recursion.
    """
    key = f"({source.key_expr})"
    parent = f"({source.parent_expr})"
    tree = (
        f"WITH RECURSIVE {_CTE_NAME}({_CTE_COLUMN_NAME}) AS ("
        f"SELECT {key} FROM {source.relation_sql} WHERE {parent} IN ({value_sql}) "
        f"UNION "
        f"SELECT {key} FROM {source.relation_sql} "
        f"JOIN {_CTE_NAME} ON {parent} = {_CTE_NAME}.{_CTE_COLUMN_NAME}"
        f") SELECT {_CTE_COLUMN_NAME} FROM {_CTE_NAME}"
    )
    return f"({column_name} IN ({value_sql}) OR {column_name} IN ({tree}))"
