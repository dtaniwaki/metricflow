from __future__ import annotations

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.dimension_value_attributes import add_dimension_value_attributes
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dimension_spec import DimensionSpec
from metricflow_semantics.specs.query_spec import MetricFlowQuerySpec
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.snapshot_helpers import assert_object_snapshot_equal

from metricflow_semantic_interfaces.references import EntityReference


@pytest.fixture(scope="module")
def query_parser(
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> MetricFlowQueryParser:
    """Query parser for the manifest with `sort_by` and `label_by`."""
    return MetricFlowQueryParser(dimension_value_columns_manifest_lookup)


def _expand(
    query_parser: MetricFlowQueryParser,
    manifest_lookup: SemanticManifestLookup,
    group_by_names: list[str],
    order_by_names: list[str] | None = None,
) -> MetricFlowQuerySpec:
    query_spec = query_parser.parse_and_validate_query(
        group_by_names=group_by_names, order_by_names=order_by_names
    ).query_spec
    return add_dimension_value_attributes(
        query_spec=query_spec,
        dimension_lookup=manifest_lookup.semantic_model_lookup.dimension_lookup,
        query_parser=query_parser,
    ).query_spec


def _product_dimension_spec(name: str) -> DimensionSpec:
    return DimensionSpec(element_name=name, entity_links=(EntityReference("product"),))


def test_label_and_sort_are_added_after_the_dimension(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """The label and sort dimensions are added with the entity links of the queried dimension."""
    query_spec = _expand(
        query_parser, dimension_value_columns_manifest_lookup, ["product__color", "product__category_code"]
    )

    assert_object_snapshot_equal(
        request=request, snapshot_configuration=mf_test_configuration, obj_id="obj_0", obj=query_spec
    )


def test_sort_by_is_the_default_order(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """Without an order-by, the result is ordered by the sort dimension with the dimension breaking ties."""
    query_spec = _expand(query_parser, dimension_value_columns_manifest_lookup, ["product__category_code"])

    assert [(order_by.instance_spec, order_by.descending) for order_by in query_spec.order_by_specs] == [
        (_product_dimension_spec("category_rank"), False),
        (_product_dimension_spec("category_code"), False),
    ]


def test_label_only_has_no_default_order(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """A dimension that declares only `label_by` keeps the query without an order-by."""
    query_spec = _expand(query_parser, dimension_value_columns_manifest_lookup, ["product__brand_code"])

    assert query_spec.dimension_specs == (
        _product_dimension_spec("brand_code"),
        _product_dimension_spec("brand_name"),
    )
    assert query_spec.order_by_specs == ()


def test_dimension_without_declaration_is_unchanged(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """A dimension that does not declare `sort_by` and `label_by` gets no additional group-by items."""
    query_spec = query_parser.parse_and_validate_query(group_by_names=["product__color"]).query_spec

    assert (
        add_dimension_value_attributes(
            query_spec=query_spec,
            dimension_lookup=dimension_value_columns_manifest_lookup.semantic_model_lookup.dimension_lookup,
            query_parser=query_parser,
        ).query_spec
        == query_spec
    )


def test_explicit_order_by_is_kept(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """An order-by in the query is not replaced by the order of `sort_by`."""
    query_spec = _expand(
        query_parser,
        dimension_value_columns_manifest_lookup,
        ["product__category_code"],
        order_by_names=["-product__category_code"],
    )

    assert [(order_by.instance_spec, order_by.descending) for order_by in query_spec.order_by_specs] == [
        (_product_dimension_spec("category_code"), True),
    ]


def test_queried_attribute_is_not_added_twice(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """A label or sort dimension that is already queried is not added again."""
    query_spec = _expand(
        query_parser,
        dimension_value_columns_manifest_lookup,
        ["product__category_name", "product__category_code"],
    )

    assert query_spec.dimension_specs == (
        _product_dimension_spec("category_name"),
        _product_dimension_spec("category_code"),
        _product_dimension_spec("category_rank"),
    )
    assert query_spec.input_spec_order.group_by_item_specs == query_spec.dimension_specs


def test_attribute_spec_sets_describe_each_queried_dimension(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """The spec sets tell which added specs belong to which queried dimension."""
    query_spec = query_parser.parse_and_validate_query(
        group_by_names=["product__color", "product__brand_code", "product__category_code"]
    ).query_spec

    spec_sets = add_dimension_value_attributes(
        query_spec=query_spec,
        dimension_lookup=dimension_value_columns_manifest_lookup.semantic_model_lookup.dimension_lookup,
        query_parser=query_parser,
    ).attribute_spec_sets

    assert [(spec_set.dimension_spec, spec_set.label_spec, spec_set.sort_spec) for spec_set in spec_sets] == [
        (_product_dimension_spec("color"), None, None),
        (_product_dimension_spec("brand_code"), _product_dimension_spec("brand_name"), None),
        (
            _product_dimension_spec("category_code"),
            _product_dimension_spec("category_name"),
            _product_dimension_spec("category_rank"),
        ),
    ]


def test_dimension_of_model_without_declaration_gets_no_attributes(
    query_parser: MetricFlowQueryParser,
    dimension_value_columns_manifest_lookup: SemanticManifestLookup,
) -> None:
    """A dimension reached through a model that does not declare `sort_by` and `label_by` has no attributes."""
    query_spec = query_parser.parse_and_validate_query(group_by_names=["sale__category_code"]).query_spec

    dimension_value_query_spec = add_dimension_value_attributes(
        query_spec=query_spec,
        dimension_lookup=dimension_value_columns_manifest_lookup.semantic_model_lookup.dimension_lookup,
        query_parser=query_parser,
    )

    assert dimension_value_query_spec.query_spec == query_spec
    assert [
        (spec_set.label_spec, spec_set.sort_spec) for spec_set in dimension_value_query_spec.attribute_spec_sets
    ] == [(None, None)]
