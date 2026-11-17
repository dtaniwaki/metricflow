from __future__ import annotations

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.model.semantics.dimension_lookup import DimensionLookup
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.snapshot_helpers import assert_object_snapshot_equal

from metricflow_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow_semantic_interfaces.references import DimensionReference


@pytest.fixture(scope="module")
def dimension_lookup(  # noqa: D103
    partitioned_multi_hop_join_semantic_manifest: PydanticSemanticManifest,
) -> DimensionLookup:
    return DimensionLookup(partitioned_multi_hop_join_semantic_manifest.semantic_models)


def test_get_invariant(
    request: FixtureRequest,
    mf_test_configuration: MetricFlowTestConfiguration,
    partitioned_multi_hop_join_semantic_manifest: PydanticSemanticManifest,
    dimension_lookup: DimensionLookup,
) -> None:
    """Test invariants for all dimensions.

    Uses `partitioned_multi_hop_join_semantic_manifest` to show an example of different `is_partition` values.
    """
    dimension_references = []
    for semantic_model in partitioned_multi_hop_join_semantic_manifest.semantic_models:
        for dimension in semantic_model.dimensions:
            dimension_references.append(dimension.reference)

    sorted_dimension_references = sorted(dimension_references)
    result = {
        dimension_reference.element_name: dimension_lookup.get_invariant(dimension_reference)
        for dimension_reference in sorted_dimension_references
    }
    assert_object_snapshot_equal(
        request=request, snapshot_configuration=mf_test_configuration, obj_id="obj_0", obj=result
    )


def test_get_invariant_with_sort_by_and_label_by(
    dimension_value_columns_manifest: PydanticSemanticManifest,
) -> None:
    """The `sort_by` and `label_by` declarations are part of the invariant."""
    dimension_lookup = DimensionLookup(dimension_value_columns_manifest.semantic_models)

    category_code_invariant = dimension_lookup.get_invariant(DimensionReference("category_code"))
    assert category_code_invariant.sort_by == DimensionReference("category_rank")
    assert category_code_invariant.label_by == DimensionReference("category_name")

    brand_code_invariant = dimension_lookup.get_invariant(DimensionReference("brand_code"))
    assert brand_code_invariant.sort_by is None
    assert brand_code_invariant.label_by == DimensionReference("brand_name")

    color_invariant = dimension_lookup.get_invariant(DimensionReference("color"))
    assert color_invariant.sort_by is None
    assert color_invariant.label_by is None


@pytest.mark.parametrize("reverse_models", (False, True))
def test_get_invariant_takes_declarations_from_the_declaring_model(
    dimension_value_columns_manifest: PydanticSemanticManifest, reverse_models: bool
) -> None:
    """A model that does not declare `sort_by` or `label_by` does not hide the declaration of another model."""
    semantic_models = list(dimension_value_columns_manifest.semantic_models)
    if reverse_models:
        semantic_models.reverse()
    dimension_lookup = DimensionLookup(semantic_models)

    category_code_invariant = dimension_lookup.get_invariant(DimensionReference("category_code"))
    assert category_code_invariant.sort_by == DimensionReference("category_rank")
    assert category_code_invariant.label_by == DimensionReference("category_name")


@pytest.mark.parametrize("attribute_name", ("sort_by", "label_by"))
def test_different_declarations_are_rejected(
    dimension_value_columns_manifest: PydanticSemanticManifest, attribute_name: str
) -> None:
    """Models that declare different `sort_by` or `label_by` for the same dimension name can't be merged."""
    manifest = dimension_value_columns_manifest.copy(deep=True)
    sales_model = next(model for model in manifest.semantic_models if model.name == "sales_source")
    category_code = next(dimension for dimension in sales_model.dimensions if dimension.name == "category_code")
    setattr(category_code, attribute_name, "other_name")

    with pytest.raises(ValueError, match="conflicting values"):
        DimensionLookup(manifest.semantic_models)
