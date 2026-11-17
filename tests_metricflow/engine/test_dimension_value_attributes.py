from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Optional

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.errors.error_classes import InvalidQueryException
from metricflow_semantics.query.dimension_value_attributes import add_dimension_value_attributes
from metricflow_semantics.specs.dimension_spec import DimensionSpec
from metricflow_semantics.specs.query_spec import MetricFlowQuerySpec
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.snapshot_helpers import assert_plan_snapshot_text_equal

from metricflow.engine.metricflow_engine import (
    AbstractMetricFlowEngine,
    MetricFlowEngine,
    MetricFlowQueryRequest,
    MetricFlowQueryType,
)
from metricflow.engine.models import DimensionValue
from metricflow.protocols.sql_client import SqlClient
from metricflow_semantic_interfaces.references import EntityReference
from tests_metricflow.dataflow_plan_to_svg import display_graph_if_requested
from tests_metricflow.fixtures.manifest_fixtures import MetricFlowEngineTestFixture, SemanticManifestSetup
from tests_metricflow.query_rendering.compare_rendered_query import render_and_check


@pytest.fixture
def fixture(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture]
) -> MetricFlowEngineTestFixture:
    """Test fixture for the manifest with `sort_by` and `label_by`."""
    return mf_engine_test_fixture_mapping[SemanticManifestSetup.DIMENSION_VALUE_COLUMNS_MANIFEST]


@pytest.fixture
def engine(fixture: MetricFlowEngineTestFixture, create_source_tables: None) -> MetricFlowEngine:  # noqa: D103
    return fixture.metricflow_engine


def _expanded_query_spec(fixture: MetricFlowEngineTestFixture, group_by_name: str) -> MetricFlowQuerySpec:
    return add_dimension_value_attributes(
        query_spec=fixture.query_parser.parse_and_validate_query(group_by_names=(group_by_name,)).query_spec,
        dimension_lookup=fixture.semantic_manifest_lookup.semantic_model_lookup.dimension_lookup,
        query_parser=fixture.query_parser,
    ).query_spec


@pytest.mark.sql_engine_snapshot
def test_dimension_values_plan_with_sort_by_and_label_by(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    fixture: MetricFlowEngineTestFixture,
) -> None:
    """The plan for the values of a dimension that declares `sort_by` and `label_by` orders by `sort_by`."""
    dataflow_plan = fixture.dataflow_plan_builder.build_plan_for_distinct_values(
        _expanded_query_spec(fixture, "product__category_code")
    )

    assert_plan_snapshot_text_equal(
        request=request,
        snapshot_configuration=mf_test_configuration,
        plan=dataflow_plan,
        plan_snapshot_text=dataflow_plan.structure_text(),
    )
    display_graph_if_requested(request=request, mf_test_configuration=mf_test_configuration, dag_graph=dataflow_plan)


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_dimension_values_query_with_sort_by_and_label_by(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    fixture: MetricFlowEngineTestFixture,
    sql_client: SqlClient,
) -> None:
    """The query for the values of a dimension that declares `sort_by` and `label_by` selects the label and sort."""
    render_and_check(
        request=request,
        mf_test_configuration=mf_test_configuration,
        dataflow_to_sql_converter=fixture.dataflow_to_sql_converter,
        sql_client=sql_client,
        dataflow_plan_builder=fixture.dataflow_plan_builder,
        query_spec=_expanded_query_spec(fixture, "product__category_code"),
    )


def test_values_are_ordered_by_sort_by(engine: MetricFlowEngine) -> None:
    """Values come with the label and sort key, ordered by the sort key instead of the value."""
    assert engine.get_dimension_values_with_attributes(
        metric_names=[], get_group_by_values="product__category_code"
    ) == [
        DimensionValue(value="ELEC", label="Electronics", sort_key=1),
        DimensionValue(value="TOYS", label="Toys", sort_key=2),
        DimensionValue(value="BOOK", label="Books", sort_key=3),
    ]


def test_get_dimension_values_follows_sort_by(engine: MetricFlowEngine) -> None:
    """`get_dimension_values` returns only the values, in the order of `sort_by`."""
    assert engine.get_dimension_values(metric_names=[], get_group_by_values="product__category_code") == [
        "ELEC",
        "TOYS",
        "BOOK",
    ]


def test_label_by_without_sort_by_is_ordered_by_value(engine: MetricFlowEngine) -> None:
    """Without `sort_by`, values are ordered by value."""
    assert engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="product__brand_code") == [
        DimensionValue(value="b1", label="Acme"),
        DimensionValue(value="b2", label="Zenith"),
    ]


def test_dimension_without_declaration_has_no_attributes(engine: MetricFlowEngine) -> None:
    """A dimension that declares neither `sort_by` nor `label_by` returns the same values as before."""
    assert engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="product__color") == [
        DimensionValue(value="blue"),
        DimensionValue(value="green"),
        DimensionValue(value="red"),
    ]
    assert engine.get_dimension_values(metric_names=[], get_group_by_values="product__color") == [
        "blue",
        "green",
        "red",
    ]


def test_dimension_of_model_without_declaration_has_no_attributes(engine: MetricFlowEngine) -> None:
    """The model that owns the dimension declares nothing, so the declaration of another model with the same name is not used."""
    assert engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="sale__category_code") == [
        DimensionValue(value="BOOK"),
        DimensionValue(value="ELEC"),
        DimensionValue(value="TOYS"),
    ]
    assert engine.get_dimension_values(metric_names=[], get_group_by_values="sale__brand_code") == ["b1", "b2"]


def test_values_with_metrics_have_no_attributes(engine: MetricFlowEngine) -> None:
    """The values of a query with metrics are neither extended with the label and sort key nor ordered by them."""
    assert engine.get_dimension_values_with_attributes(
        metric_names=["sales"], get_group_by_values="product__category_code"
    ) == [
        DimensionValue(value="ELEC"),
        DimensionValue(value="TOYS"),
    ]


def test_value_with_multiple_labels_is_rejected(engine: MetricFlowEngine) -> None:
    """A value with more than one distinct label is an error since the label can't be chosen."""
    with pytest.raises(InvalidQueryException, match="multiple distinct labels or sort keys"):
        engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="product__region_code")


def test_value_with_null_and_non_null_label_is_rejected(engine: MetricFlowEngine) -> None:
    """A missing label for a value that has another label is not ignored."""
    with pytest.raises(InvalidQueryException, match="multiple distinct labels or sort keys"):
        engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="product__store_code")


def test_value_with_multiple_sort_keys_is_rejected(engine: MetricFlowEngine) -> None:
    """A value with more than one distinct sort key is an error even though it has no label."""
    with pytest.raises(InvalidQueryException, match="multiple distinct labels or sort keys"):
        engine.get_dimension_values_with_attributes(metric_names=[], get_group_by_values="product__shelf_code")


@pytest.mark.parametrize("metric_names", (["sales"], []))
def test_metric_query_is_not_extended(engine: MetricFlowEngine, metric_names: list[str]) -> None:
    """Only the dimension values query gets the label and sort of the dimension, with or without metrics."""
    result = engine.explain(
        MetricFlowQueryRequest.create(
            metric_names=metric_names,
            group_by_names=["product__category_code"],
            query_type=MetricFlowQueryType.METRIC,
        )
    )

    assert result.query_spec.dimension_specs == (
        DimensionSpec(element_name="category_code", entity_links=(EntityReference("product"),)),
    )
    assert result.query_spec.order_by_specs == ()
    assert result.dimension_value_attribute_spec_sets == ()


def test_min_max_only_is_not_extended(engine: MetricFlowEngine) -> None:
    """The minimum and maximum of a dimension are not computed together with its label and sort."""
    explain_result = engine.explain_get_dimension_values(
        get_group_by_values="product__category_code",
        min_max_only=True,
    )

    assert explain_result.query_spec.dimension_specs == (
        DimensionSpec(element_name="category_code", entity_links=(EntityReference("product"),)),
    )
    assert explain_result.query_spec.order_by_specs == ()
    assert explain_result.dimension_value_attribute_spec_sets == ()


class _EngineWithValuesOnly:
    def get_dimension_values(
        self,
        metric_names: list[str],
        get_group_by_values: str,
        time_constraint_start: Optional[datetime.datetime] = None,
        time_constraint_end: Optional[datetime.datetime] = None,
    ) -> list[str]:
        return ["a", "b"]


def test_default_implementation_returns_values_only() -> None:
    """An engine that only implements `get_dimension_values` returns values without attributes."""
    assert AbstractMetricFlowEngine.get_dimension_values_with_attributes(
        _EngineWithValuesOnly(),  # type: ignore[arg-type]
        metric_names=[],
        get_group_by_values="product__color",
    ) == [DimensionValue(value="a"), DimensionValue(value="b")]
