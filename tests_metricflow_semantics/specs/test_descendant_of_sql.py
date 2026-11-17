from __future__ import annotations

from typing import Tuple

import pytest
from metricflow_semantics.semantic_graph.attribute_resolution.group_by_item_set import GroupByItemSet
from metricflow_semantics.specs.where_filter.descendant_of import (
    DescendantOfSource,
    render_descendant_of_sql,
)
from metricflow_semantics.specs.where_filter.where_filter_spec import WhereFilterSpec
from metricflow_semantics.sql.sql_bind_parameters import SqlBindParameterSet

from metricflow_semantic_interfaces.descendant_of_value import DescendantOfValue

_SOURCE = DescendantOfSource(relation_sql="some_schema.dim_employees", key_expr="employee_id", parent_expr="manager_id")


def test_render_descendant_of_sql() -> None:
    """The condition accepts the value, and the keys reached by following parents down from it."""
    assert render_descendant_of_sql("employee__employee_key", _SOURCE, "'e1'") == (
        "(employee__employee_key IN ('e1') OR employee__employee_key IN ("
        "WITH RECURSIVE descendant_of_tree(descendant_of_value) AS ("
        "SELECT (employee_id) FROM some_schema.dim_employees WHERE (manager_id) IN ('e1') "
        "UNION "
        "SELECT (employee_id) FROM some_schema.dim_employees "
        "JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value"
        ") SELECT descendant_of_value FROM descendant_of_tree))"
    )


@pytest.mark.parametrize("value", ["a%b", "a:b", "x:y%z"])
def test_value_with_percent_or_colon_is_written_as_is(value: str) -> None:  # noqa: D103
    sql = render_descendant_of_sql("employee__employee_key", _SOURCE, DescendantOfValue.create(value).sql)

    assert sql.count(f"IN ('{value}')") == 2
    assert sql.count(value) == 2


@pytest.mark.parametrize("value,expected_sql", [("e1", "'e1'"), (7, "7")])
def test_descendant_of_value_literal(value: object, expected_sql: str) -> None:  # noqa: D103
    assert DescendantOfValue.create(value) == DescendantOfValue(sql=expected_sql)


def test_where_filter_spec_has_descendant_of_only_with_sources() -> None:  # noqa: D103
    def create_spec(sources: Tuple[DescendantOfSource, ...]) -> WhereFilterSpec:
        return WhereFilterSpec(
            where_sql="x = 1",
            bind_parameters=SqlBindParameterSet(),
            element_set=GroupByItemSet(),
            descendant_of_sources=sources,
        )

    assert create_spec((_SOURCE,)).has_descendant_of
    assert not create_spec(()).has_descendant_of
