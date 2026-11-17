from __future__ import annotations

from typing import Optional, Sequence

import pytest

from metricflow_semantic_interfaces.implementations.elements.dimension import (
    PydanticDimension,
    PydanticDimensionTypeParams,
)
from metricflow_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow_semantic_interfaces.test_utils import semantic_model_with_guaranteed_meta
from metricflow_semantic_interfaces.type_enums import DimensionType, TimeGranularity
from metricflow_semantic_interfaces.validations.dimension_value_column import DimensionValueColumnRule
from metricflow_semantic_interfaces.validations.semantic_manifest_validator import SemanticManifestValidator
from metricflow_semantic_interfaces.validations.validator_helpers import SemanticManifestValidationException
from tests_metricflow_semantic_interfaces.example_project_configuration import EXAMPLE_PROJECT_CONFIGURATION


def _validate(dimensions: Sequence[PydanticDimension]) -> None:
    SemanticManifestValidator[PydanticSemanticManifest]([DimensionValueColumnRule()]).checked_validations(
        PydanticSemanticManifest(
            semantic_models=[semantic_model_with_guaranteed_meta(name="product", dimensions=list(dimensions))],
            metrics=[],
            project_configuration=EXAMPLE_PROJECT_CONFIGURATION,
        )
    )


def _categorical(name: str, sort_by: Optional[str] = None, label_by: Optional[str] = None) -> PydanticDimension:
    return PydanticDimension(name=name, type=DimensionType.CATEGORICAL, sort_by=sort_by, label_by=label_by)


def _time(name: str) -> PydanticDimension:
    return PydanticDimension(
        name=name,
        type=DimensionType.TIME,
        type_params=PydanticDimensionTypeParams(time_granularity=TimeGranularity.DAY),
    )


def _categorical_with_reference(name: str, attribute_name: str, referenced_name: str) -> PydanticDimension:
    if attribute_name == "sort_by":
        return _categorical(name, sort_by=referenced_name)
    return _categorical(name, label_by=referenced_name)


def test_valid_sort_by_and_label_by() -> None:  # noqa: D103
    _validate(
        [
            _categorical("category_code", sort_by="category_rank", label_by="category_name"),
            _categorical("category_rank"),
            _categorical("category_name"),
        ]
    )


@pytest.mark.parametrize("attribute_name", ("sort_by", "label_by"))
def test_unknown_dimension(attribute_name: str) -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match="is not a dimension in the same semantic model"):
        _validate([_categorical_with_reference("category_code", attribute_name, "missing")])


@pytest.mark.parametrize("attribute_name", ("sort_by", "label_by"))
def test_self_reference(attribute_name: str) -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match="is the dimension itself"):
        _validate([_categorical_with_reference("category_code", attribute_name, "category_code")])


@pytest.mark.parametrize("attribute_name", ("sort_by", "label_by"))
def test_entity_link_in_name(attribute_name: str) -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match="without entity links"):
        _validate([_categorical_with_reference("category_code", attribute_name, "product__category_rank")])


@pytest.mark.parametrize("attribute_name", ("sort_by", "label_by"))
def test_time_dimension_as_target(attribute_name: str) -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match="must be a categorical dimension"):
        _validate([_categorical_with_reference("category_code", attribute_name, "created_at"), _time("created_at")])


def test_time_dimension_as_source() -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match="can only be set on a categorical dimension"):
        _validate(
            [
                PydanticDimension(
                    name="created_at",
                    type=DimensionType.TIME,
                    type_params=PydanticDimensionTypeParams(time_granularity=TimeGranularity.DAY),
                    sort_by="category_rank",
                ),
                _categorical("category_rank"),
            ]
        )


def test_rule_is_in_the_default_rules() -> None:  # noqa: D103
    results = SemanticManifestValidator[PydanticSemanticManifest]().validate_semantic_manifest(
        PydanticSemanticManifest(
            semantic_models=[
                semantic_model_with_guaranteed_meta(
                    name="product", dimensions=[_categorical("category_code", sort_by="missing")]
                )
            ],
            metrics=[],
            project_configuration=EXAMPLE_PROJECT_CONFIGURATION,
        )
    )

    assert "has an invalid `sort_by`" in str(SemanticManifestValidationException(results.all_issues))
