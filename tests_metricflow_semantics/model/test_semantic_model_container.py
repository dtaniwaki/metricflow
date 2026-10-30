from __future__ import annotations

import logging
from typing import Dict, List

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.model.semantics.metric_lookup import MetricLookup
from metricflow_semantics.model.semantics.semantic_model_lookup import SemanticModelLookup
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.snapshot_helpers import (
    assert_object_snapshot_equal,
)
from metricflow_semantics.time.time_spine_source import TimeSpineSource
from metricflow_semantics.toolkit.collections.ordered_set import FrozenOrderedSet

from metricflow_semantic_interfaces.protocols.semantic_manifest import SemanticManifest
from metricflow_semantic_interfaces.references import EntityReference, MetricReference

logger = logging.getLogger(__name__)


def build_semantic_model_lookup_from_manifest(semantic_manifest: SemanticManifest) -> SemanticModelLookup:  # noqa: D103
    time_spine_sources = TimeSpineSource.build_standard_time_spine_sources(semantic_manifest)
    custom_granularities = TimeSpineSource.build_custom_granularities(list(time_spine_sources.values()))
    return SemanticModelLookup(semantic_manifest=semantic_manifest, custom_granularities=custom_granularities)


@pytest.fixture
def semantic_model_lookup(simple_semantic_manifest: SemanticManifest) -> SemanticModelLookup:  # noqa: D103
    return build_semantic_model_lookup_from_manifest(simple_semantic_manifest)


@pytest.fixture
def multi_hop_semantic_model_lookup(  # noqa: D103
    multi_hop_join_manifest: SemanticManifest,
) -> SemanticModelLookup:
    return build_semantic_model_lookup_from_manifest(multi_hop_join_manifest)


@pytest.fixture
def metric_lookup(simple_semantic_manifest: SemanticManifest) -> MetricLookup:  # noqa: D103
    return SemanticManifestLookup(simple_semantic_manifest).metric_lookup


@pytest.fixture
def multi_hop_metric_lookup(multi_hop_join_manifest: SemanticManifest) -> MetricLookup:  # noqa: D103
    return SemanticManifestLookup(multi_hop_join_manifest).metric_lookup


def test_get_names(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    semantic_model_lookup: SemanticModelLookup,
) -> None:
    assert_object_snapshot_equal(
        request=request,
        snapshot_configuration=mf_test_configuration,
        obj_id="result0",
        obj={
            "dimension_references": sorted([d.element_name for d in semantic_model_lookup.get_dimension_references()]),
            "entity_references": sorted([i.element_name for i in semantic_model_lookup.get_entity_references()]),
        },
    )


def test_get_semantic_models_for_entity(semantic_model_lookup: SemanticModelLookup) -> None:  # noqa: D103
    entity_reference = EntityReference(element_name="user")
    linked_semantic_models = semantic_model_lookup.get_semantic_models_for_entity(entity_reference=entity_reference)
    assert len(linked_semantic_models) == 10


def test_get_aggregation_time_dimension_specs(  # noqa: D103
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    metric_lookup: MetricLookup,
    semantic_model_lookup: SemanticModelLookup,
) -> None:
    result = {}
    for metric_name in ["views", "listings", "bookings_per_view"]:
        specs = metric_lookup.get_aggregation_time_dimension_specs(MetricReference(metric_name))
        result[metric_name] = list(spec.dunder_name for spec in specs)

    assert_object_snapshot_equal(request=request, snapshot_configuration=mf_test_configuration, obj=result)


def _day_dunder_names_by_simple_metric(metric_lookup: MetricLookup, metric_name: str) -> Dict[str, List[str]]:
    return {
        simple_metric_reference.element_name: [spec.dunder_name for spec in specs if spec.dunder_name.endswith("__day")]
        for simple_metric_reference, specs in metric_lookup.get_aggregation_time_dimension_specs_by_simple_metric(
            MetricReference(metric_name)
        ).items()
    }


@pytest.mark.parametrize(
    "metric_name,expected",
    (
        ("bookings", {"bookings": ["booking__ds__day", "metric_time__day"]}),
        ("trailing_2_months_revenue", {"revenue": ["revenue_instance__ds__day", "metric_time__day"]}),
        (
            "bookings_per_view",
            {"bookings": ["booking__ds__day", "metric_time__day"], "views": ["view__ds__day", "metric_time__day"]},
        ),
        (
            "instant_plus_non_referred_bookings_pct",
            {
                "referred_bookings": ["booking__ds__day", "metric_time__day"],
                "bookings": ["booking__ds__day", "metric_time__day"],
                "instant_bookings": ["booking__ds__day", "metric_time__day"],
            },
        ),
        (
            "visit_buy_conversion_rate",
            {
                "visits": ["visit__ds__day", "metric_time__day"],
                "buys": ["buy__ds__day", "metric_time__day"],
            },
        ),
        ("bookings_growth_since_start_of_month", {"bookings": ["booking__ds__day", "metric_time__day"]}),
    ),
)
def test_get_aggregation_time_dimension_specs_by_simple_metric(  # noqa: D103
    metric_lookup: MetricLookup, metric_name: str, expected: Dict[str, List[str]]
) -> None:
    result = _day_dunder_names_by_simple_metric(metric_lookup, metric_name)
    assert result == expected
    assert list(result) == list(expected)


def test_get_aggregation_time_dimension_specs_by_simple_metric_snapshot(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    metric_lookup: MetricLookup,
) -> None:
    """Full per-simple-metric specs for a ratio, a nested derived metric and a conversion metric."""
    result = {}
    for metric_name in ("bookings_per_view", "instant_plus_non_referred_bookings_pct", "visit_buy_conversion_rate"):
        result[metric_name] = {
            simple_metric_reference.element_name: [spec.dunder_name for spec in specs]
            for simple_metric_reference, specs in metric_lookup.get_aggregation_time_dimension_specs_by_simple_metric(
                MetricReference(metric_name)
            ).items()
        }

    assert_object_snapshot_equal(request=request, snapshot_configuration=mf_test_configuration, obj=result)


def test_get_aggregation_time_dimension_specs_by_simple_metric_is_read_only(  # noqa: D103
    metric_lookup: MetricLookup,
) -> None:
    metric_reference = MetricReference("bookings_per_view")
    result = metric_lookup.get_aggregation_time_dimension_specs_by_simple_metric(metric_reference)
    with pytest.raises(TypeError):
        result[MetricReference("views")] = FrozenOrderedSet()  # type: ignore[index]
    with pytest.raises(TypeError):
        del result[MetricReference("views")]  # type: ignore[attr-defined]

    assert list(metric_lookup.get_aggregation_time_dimension_specs_by_simple_metric(metric_reference)) == [
        MetricReference("bookings"),
        MetricReference("views"),
    ]
