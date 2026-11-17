from __future__ import annotations

import logging
from typing import Sequence

import pytest
from metricflow_semantics.errors.error_classes import InvalidQueryException
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.query_param_implementations import DimensionOrEntityParameter, OrderByParameter
from metricflow_semantics.specs.query_spec import MetricFlowQuerySpec

logger = logging.getLogger(__name__)

LOCAL_DIMENSION_NAME = "user__home_state_latest"
MULTI_HOP_DIMENSION_NAME = "listing__user__home_state_latest"


@pytest.fixture
def query_parser(simple_semantic_manifest_lookup: SemanticManifestLookup) -> MetricFlowQueryParser:  # noqa: D103
    return MetricFlowQueryParser(simple_semantic_manifest_lookup)


def _dunder_names(query_spec: MetricFlowQuerySpec) -> Sequence[str]:
    return tuple(spec.dunder_name for spec in query_spec.dimension_specs)


def test_multi_hop_dimension_keeps_its_name_with_metric(query_parser: MetricFlowQueryParser) -> None:
    """With a metric, the multi-hop name is resolved through the semantic model of the metric."""
    query_spec = query_parser.parse_and_validate_query(
        metric_names=("bookings",), group_by_names=(MULTI_HOP_DIMENSION_NAME,)
    ).query_spec
    assert _dunder_names(query_spec) == (MULTI_HOP_DIMENSION_NAME,)


def test_multi_hop_dimension_is_alias_without_metrics(query_parser: MetricFlowQueryParser) -> None:
    """Without metrics there is no semantic model to join from, so the name is an alias of the shorter name."""
    query_spec = query_parser.parse_and_validate_query(group_by_names=(MULTI_HOP_DIMENSION_NAME,)).query_spec
    assert _dunder_names(query_spec) == (LOCAL_DIMENSION_NAME,)
    assert query_spec == query_parser.parse_and_validate_query(group_by_names=(LOCAL_DIMENSION_NAME,)).query_spec


def test_multi_hop_dimension_in_where_filter_and_order_by(query_parser: MetricFlowQueryParser) -> None:
    """The same resolution applies to filters and order-by items."""
    query_spec = query_parser.parse_and_validate_query(
        group_by_names=(MULTI_HOP_DIMENSION_NAME,),
        where_constraint_strs=["{{ Dimension('user__home_state_latest', entity_path=['listing']) }} = 'CA'"],
        order_by_names=(f"-{MULTI_HOP_DIMENSION_NAME}",),
    ).query_spec
    assert _dunder_names(query_spec) == (LOCAL_DIMENSION_NAME,)
    assert [order_by.instance_spec.dunder_name for order_by in query_spec.order_by_specs] == [LOCAL_DIMENSION_NAME]
    assert query_spec.order_by_specs[0].descending
    assert query_spec.filter_spec_resolution_lookup is not None
    resolved_filter_spec_names = {
        spec.dunder_name
        for resolution in query_spec.filter_spec_resolution_lookup.spec_resolutions
        for spec in resolution.resolved_group_by_item_set.specs
    }
    assert resolved_filter_spec_names == {LOCAL_DIMENSION_NAME}


@pytest.mark.parametrize(
    ("group_by_name", "expected_name"),
    (
        pytest.param("listing__user__created_at__day", "user__created_at__day", id="time dimension with grain"),
        pytest.param("listing__user__created_at", "user__created_at__day", id="time dimension without grain"),
        pytest.param("listing__user__company", "user__company", id="entity"),
    ),
)
def test_time_dimension_and_entity_names(
    query_parser: MetricFlowQueryParser, group_by_name: str, expected_name: str
) -> None:
    """Time dimensions and entities are treated the same as categorical dimensions."""
    query_spec = query_parser.parse_and_validate_query(group_by_names=(group_by_name,)).query_spec
    assert [spec.dunder_name for spec in query_spec.linkable_specs.as_tuple] == [expected_name]


def test_order_by_with_alias(query_parser: MetricFlowQueryParser) -> None:
    """An order-by item that refers to a group-by item by its alias is resolved the same way."""
    query_spec = query_parser.parse_and_validate_query(
        group_by=(DimensionOrEntityParameter(name=MULTI_HOP_DIMENSION_NAME, alias="state"),),
        order_by=(
            OrderByParameter(
                order_by=DimensionOrEntityParameter(name=MULTI_HOP_DIMENSION_NAME, alias="state"), descending=True
            ),
        ),
    ).query_spec
    assert [order_by.instance_spec.dunder_name for order_by in query_spec.order_by_specs] == [LOCAL_DIMENSION_NAME]
    assert [spec.alias for spec in query_spec.dimension_specs] == ["state"]


def test_alias_and_original_name_in_same_query_are_duplicates(query_parser: MetricFlowQueryParser) -> None:
    """Both names resolve to the same output column, which is reported as a duplicate."""
    with pytest.raises(InvalidQueryException, match="duplicate output column names: \\('user__home_state_latest',\\)"):
        query_parser.parse_and_validate_query(group_by_names=(MULTI_HOP_DIMENSION_NAME, LOCAL_DIMENSION_NAME))


@pytest.mark.parametrize(
    "group_by_name",
    (
        pytest.param("bogus__user__home_state_latest", id="leading link is not an entity"),
        pytest.param("user__listing__country_latest", id="join in a direction that does not exist"),
        pytest.param("user__user__home_state_latest", id="entity joined to itself"),
        pytest.param("listing__listing__country_latest", id="entity that exists but has no such path"),
        pytest.param("booking__listing__user__home_state_latest", id="more entity links than joins allow"),
        pytest.param("user__user__created_at__day", id="time dimension joined to itself"),
        pytest.param("listing__user__not_a_dimension", id="unknown dimension"),
        pytest.param("listing__user__listing", id="unknown element for the last link"),
        pytest.param("home_state_latest", id="no entity link"),
    ),
)
def test_names_that_do_not_resolve_without_metrics(query_parser: MetricFlowQueryParser, group_by_name: str) -> None:
    """Names that are not valid with joins stay errors, and the error uses the name that was given."""
    with pytest.raises(InvalidQueryException, match="does not match any of the available group-by-items") as e:
        query_parser.parse_and_validate_query(group_by_names=(group_by_name,))
    assert f"Query Input:\n\n    {group_by_name}\n" in str(e.value)


def test_order_by_name_that_is_not_valid_with_joins(query_parser: MetricFlowQueryParser) -> None:
    """An order-by item is only resolved through a shorter name if the longer name is valid with joins."""
    with pytest.raises(InvalidQueryException, match="does not match exactly one of the query items"):
        query_parser.parse_and_validate_query(
            group_by_names=(LOCAL_DIMENSION_NAME,), order_by_names=("user__user__home_state_latest",)
        )


def test_leading_entity_links_are_not_dropped_for_order_by_with_metrics(query_parser: MetricFlowQueryParser) -> None:
    """With a metric, an order-by item must match exactly the group-by items of the query."""
    with pytest.raises(InvalidQueryException, match="does not match exactly one of the query items"):
        query_parser.parse_and_validate_query(
            metric_names=("views",),
            group_by_names=(LOCAL_DIMENSION_NAME,),
            order_by_names=(MULTI_HOP_DIMENSION_NAME,),
        )
