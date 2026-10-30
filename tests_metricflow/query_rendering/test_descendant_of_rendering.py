from __future__ import annotations

import logging
from collections.abc import Mapping

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.errors.error_classes import (
    InvalidDescendantOfError,
    InvalidQueryException,
    UnsupportedEngineFeatureError,
)
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration

from metricflow.dataflow.dataflow_plan import DataflowPlan
from metricflow.protocols.sql_client import SqlClient, SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from tests_metricflow.fixtures.manifest_fixtures import MetricFlowEngineTestFixture, SemanticManifestSetup
from tests_metricflow.query_rendering.compare_rendered_query import render_and_check


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_with_metric(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
    sql_client: SqlClient,
) -> None:
    """Check the SQL for a where filter that limits an employee to one employee and the ones reporting to them."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    render_and_check(
        request=request,
        mf_test_configuration=mf_test_configuration,
        dataflow_to_sql_converter=fixture.dataflow_to_sql_converter,
        sql_client=sql_client,
        dataflow_plan_builder=fixture.dataflow_plan_builder,
        query_spec=fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__employee_key"],
            where_constraint_strs=["{{ Dimension('employee__employee_key').descendant_of('e2') }}"],
        ).query_spec,
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_with_integer_value(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
    sql_client: SqlClient,
) -> None:
    """Check that an integer value is written as a number, not a string."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    render_and_check(
        request=request,
        mf_test_configuration=mf_test_configuration,
        dataflow_to_sql_converter=fixture.dataflow_to_sql_converter,
        sql_client=sql_client,
        dataflow_plan_builder=fixture.dataflow_plan_builder,
        query_spec=fixture.query_parser.parse_and_validate_query(
            group_by_names=["employee__employee_key"],
            where_constraint_strs=["{{ Dimension('employee__employee_key').descendant_of(7) }}"],
        ).query_spec,
    )


_RECURSIVE_CTE_EXPECTED_TO_WORK = {
    SqlEngine.DUCKDB: True,
    SqlEngine.POSTGRES: True,
    SqlEngine.SNOWFLAKE: False,
    SqlEngine.BIGQUERY: False,
    SqlEngine.DATABRICKS: False,
    SqlEngine.REDSHIFT: False,
    SqlEngine.TRINO: False,
    SqlEngine.VERTICA: False,
    SqlEngine.ATHENA: False,
    SqlEngine.CLICKHOUSE: False,
}


def test_every_engine_has_an_expectation() -> None:
    """Check that adding an engine requires deciding whether it can run descendant_of."""
    assert set(_RECURSIVE_CTE_EXPECTED_TO_WORK) == set(SqlEngine)


def _descendant_of_dataflow_plan(fixture: MetricFlowEngineTestFixture) -> DataflowPlan:
    return fixture.dataflow_plan_builder.build_plan(
        fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__employee_key"],
            where_constraint_strs=["{{ Dimension('employee__employee_key').descendant_of('e2') }}"],
        ).query_spec,
    )


@pytest.mark.duckdb_only
@pytest.mark.parametrize("sql_engine", list(SqlEngine), ids=lambda engine: engine.value)
@pytest.mark.parametrize("optimization_level", [SqlOptimizationLevel.O0, SqlOptimizationLevel.O5])
def test_descendant_of_by_engine(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
    sql_engine: SqlEngine,
    optimization_level: SqlOptimizationLevel,
) -> None:
    """Check that an engine that is not known to support the recursive query fails with a clear error."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    dataflow_plan = _descendant_of_dataflow_plan(fixture)

    def convert() -> None:
        fixture.dataflow_to_sql_converter.convert_to_sql_plan(
            sql_engine_type=sql_engine,
            dataflow_plan_node=dataflow_plan.sink_node,
            optimization_level=optimization_level,
        )

    if _RECURSIVE_CTE_EXPECTED_TO_WORK[sql_engine]:
        convert()
    else:
        with pytest.raises(UnsupportedEngineFeatureError, match="descendant_of"):
            convert()


@pytest.mark.duckdb_only
def test_unsupported_engine_is_not_retried_at_a_lower_optimization_level(
    caplog: pytest.LogCaptureFixture,
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
) -> None:
    """Check that the error is raised on the first attempt instead of being logged as a bug and retried."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    with pytest.raises(UnsupportedEngineFeatureError), caplog.at_level(logging.ERROR):
        fixture.dataflow_to_sql_converter.convert_to_sql_plan(
            sql_engine_type=SqlEngine.SNOWFLAKE,
            dataflow_plan_node=_descendant_of_dataflow_plan(fixture).sink_node,
            optimization_level=SqlOptimizationLevel.O5,
        )
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.duckdb_only
@pytest.mark.parametrize("use_cte", [False, True])
def test_descendant_of_is_rejected_by_convert_using_specifics(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
    use_cte: bool,
) -> None:
    """Check that the entry point that takes the options directly also rejects, with or without CTEs."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    sink_node = _descendant_of_dataflow_plan(fixture).sink_node
    with pytest.raises(UnsupportedEngineFeatureError, match="descendant_of"):
        fixture.dataflow_to_sql_converter.convert_using_specifics(
            sql_engine_type=SqlEngine.SNOWFLAKE,
            dataflow_plan_node=sink_node,
            sql_query_plan_id=None,
            nodes_to_convert_to_cte=frozenset({sink_node.parent_nodes[0]}) if use_cte else frozenset(),
            optimizers=(),
        )


@pytest.mark.duckdb_only
@pytest.mark.parametrize(
    "where_constraint_str,expected_message",
    [
        (
            "{{ Dimension('employee__employee_name').descendant_of('Alice') }}",
            "not a level with a parent",
        ),
        (
            "{{ Dimension('task__task_kind').descendant_of('plan') }}",
            "not a level with a parent",
        ),
        (
            "{{ Dimension('employee__employee_key').descendant_of(\"it's\") }}",
            "single quote",
        ),
    ],
)
def test_descendant_of_on_a_dimension_without_hierarchy(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
    where_constraint_str: str,
    expected_message: str,
) -> None:
    """Check that a dimension that is not a level with a parent gets an error that says why."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    with pytest.raises(InvalidQueryException, match=expected_message):
        fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__employee_key"],
            where_constraint_strs=[where_constraint_str],
        )


@pytest.mark.duckdb_only
def test_a_value_that_looks_like_the_recursive_subquery_is_not_a_descendant_of(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
) -> None:
    """Check that only descendant_of is rejected, not a plain filter whose text contains the same SQL."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    dataflow_plan = fixture.dataflow_plan_builder.build_plan(
        fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__employee_key"],
            where_constraint_strs=[
                "{{ Dimension('employee__employee_key') }} = 'WITH RECURSIVE descendant_of_tree(descendant_of_value)'"
            ],
        ).query_spec,
    )
    fixture.dataflow_to_sql_converter.convert_to_sql_plan(
        sql_engine_type=SqlEngine.SNOWFLAKE, dataflow_plan_node=dataflow_plan.sink_node
    )


@pytest.mark.duckdb_only
def test_descendant_of_refusal_has_its_own_error_type(
    mf_engine_test_fixture_mapping: Mapping[SemanticManifestSetup, MetricFlowEngineTestFixture],
) -> None:
    """Check that the refusal can be told apart from other query errors without reading its message."""
    fixture = mf_engine_test_fixture_mapping[SemanticManifestSetup.HIERARCHY_MANIFEST]
    with pytest.raises(InvalidDescendantOfError):
        fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__employee_key"],
            where_constraint_strs=["{{ Dimension('employee__employee_name').descendant_of('Alice') }}"],
        )

    with pytest.raises(InvalidQueryException) as other_error:
        fixture.query_parser.parse_and_validate_query(
            metric_names=["task_hours"],
            group_by_names=["employee__nope"],
        )
    assert type(other_error.value) is InvalidQueryException
