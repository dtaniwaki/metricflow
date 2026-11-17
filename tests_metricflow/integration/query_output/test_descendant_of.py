from __future__ import annotations

from typing import Optional, Sequence

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration

from metricflow.engine.metricflow_engine import MetricFlowQueryRequest
from metricflow.protocols.sql_client import SqlClient
from tests_metricflow.integration.conftest import IntegrationTestHelpers
from tests_metricflow.snapshot_utils import assert_str_snapshot_equal

EMPLOYEE_KEY = "{{ Dimension('employee__employee_key') }}"


def _check_query_output(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
    where_constraints: Sequence[str],
    metric_names: Optional[Sequence[str]] = None,
) -> None:
    query_result = hierarchy_it_helpers.mf_engine.query(
        MetricFlowQueryRequest.create(
            metric_names=metric_names,
            group_by_names=["employee__employee_key"],
            order_by_names=["employee__employee_key"],
            where_constraints=where_constraints,
        )
    )
    assert query_result.result_df is not None, "Unexpected empty result."

    assert_str_snapshot_equal(
        request=request,
        mf_test_configuration=mf_test_configuration,
        snapshot_id="query_output",
        snapshot_str=query_result.result_df.text_format(),
        sql_engine=sql_client.sql_engine_type,
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_includes_start_and_reaches_grandchildren(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('e2') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_with_metric(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('e1') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_combined_with_or(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=[
            "{{ Dimension('employee__employee_key').descendant_of('e4') }} OR " f"{EMPLOYEE_KEY} = 'e8'"
        ],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_multiple_descendant_of_in_one_filter(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=[
            "{{ Dimension('employee__employee_key').descendant_of('e1') }} AND NOT "
            "{{ Dimension('employee__employee_key').descendant_of('e2') }}"
        ],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_multiple_descendant_of_filters(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=[
            "{{ Dimension('employee__employee_key').descendant_of('e1') }}",
            "{{ Dimension('employee__employee_key').descendant_of('e2') }}",
        ],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_stops_on_cyclic_parents(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('c1') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_in_metric_filter(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["filtered_task_hours"],
        where_constraints=[],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_start_that_only_appears_as_a_parent(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('o0') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_start_that_has_a_row_and_is_a_parent(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('o1') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
def test_descendant_of_start_without_any_row(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('nobody') }}"],
    )


@pytest.mark.sql_engine_snapshot
@pytest.mark.duckdb_only
@pytest.mark.parametrize("start", ["a%b", "a:b"], ids=["percent", "colon"])
def test_descendant_of_value_with_percent_or_colon(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    sql_client: SqlClient,
    hierarchy_it_helpers: IntegrationTestHelpers,
    start: str,
) -> None:
    _check_query_output(
        request,
        mf_test_configuration,
        sql_client,
        hierarchy_it_helpers,
        metric_names=["task_hours"],
        where_constraints=["{{ Dimension('employee__employee_key').descendant_of('" + start + "') }}"],
    )
