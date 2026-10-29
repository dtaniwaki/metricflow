from __future__ import annotations

from typing import Dict

import pytest

from metricflow_semantic_interfaces.implementations.elements.dimension import (
    PydanticDimension,
    PydanticDimensionTypeParams,
)
from metricflow_semantic_interfaces.implementations.elements.measure import PydanticMeasure
from metricflow_semantic_interfaces.implementations.metric import (
    PydanticMetricInputMeasure,
    PydanticMetricTypeParams,
)
from metricflow_semantic_interfaces.implementations.semantic_manifest import (
    PydanticSemanticManifest,
)
from metricflow_semantic_interfaces.test_utils import (
    metric_with_guaranteed_meta,
    semantic_model_with_guaranteed_meta,
)
from metricflow_semantic_interfaces.type_enums import (
    AggregationType,
    DimensionType,
    MetricType,
    TimeGranularity,
)
from metricflow_semantic_interfaces.validations.dimension_const import DimensionConsistencyRule
from metricflow_semantic_interfaces.validations.semantic_manifest_validator import (
    SemanticManifestValidator,
)
from metricflow_semantic_interfaces.validations.validator_helpers import (
    SemanticManifestValidationException,
)
from tests_metricflow_semantic_interfaces.example_project_configuration import EXAMPLE_PROJECT_CONFIGURATION


def test_incompatible_dimension_type() -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match=r"type conflict for dimension"):
        dim_name = "dim"
        measure_name = "measure"
        model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
        model_validator.checked_validations(
            PydanticSemanticManifest(
                semantic_models=[
                    semantic_model_with_guaranteed_meta(
                        name="dim1",
                        measures=[PydanticMeasure(name=measure_name, agg=AggregationType.SUM)],
                        dimensions=[
                            PydanticDimension(
                                name=dim_name,
                                type=DimensionType.TIME,
                                type_params=PydanticDimensionTypeParams(
                                    time_granularity=TimeGranularity.DAY,
                                ),
                            )
                        ],
                    ),
                    semantic_model_with_guaranteed_meta(
                        name="categoricaldim",
                        dimensions=[PydanticDimension(name=dim_name, type=DimensionType.CATEGORICAL)],
                    ),
                ],
                metrics=[
                    metric_with_guaranteed_meta(
                        name=measure_name,
                        type=MetricType.SIMPLE,
                        type_params=PydanticMetricTypeParams(measure=PydanticMetricInputMeasure(name=measure_name)),
                    )
                ],
                project_configuration=EXAMPLE_PROJECT_CONFIGURATION,
            )
        )


def test_incompatible_dimension_is_partition() -> None:  # noqa: D103
    with pytest.raises(SemanticManifestValidationException, match=r"conflicting is_partition attribute for dimension"):
        dim_name = "dim1"
        measure_name = "measure"
        model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
        model_validator.checked_validations(
            PydanticSemanticManifest(
                semantic_models=[
                    semantic_model_with_guaranteed_meta(
                        name="dim1",
                        measures=[PydanticMeasure(name=measure_name, agg=AggregationType.SUM)],
                        dimensions=[
                            PydanticDimension(
                                name=dim_name,
                                type=DimensionType.TIME,
                                is_partition=True,
                                type_params=PydanticDimensionTypeParams(
                                    time_granularity=TimeGranularity.DAY,
                                ),
                            )
                        ],
                    ),
                    semantic_model_with_guaranteed_meta(
                        name="dim2",
                        dimensions=[
                            PydanticDimension(
                                name=dim_name,
                                type=DimensionType.TIME,
                                is_partition=False,
                                type_params=PydanticDimensionTypeParams(
                                    time_granularity=TimeGranularity.DAY,
                                ),
                            )
                        ],
                    ),
                ],
                metrics=[
                    metric_with_guaranteed_meta(
                        name=measure_name,
                        type=MetricType.SIMPLE,
                        type_params=PydanticMetricTypeParams(measure=PydanticMetricInputMeasure(name=measure_name)),
                    )
                ],
                project_configuration=EXAMPLE_PROJECT_CONFIGURATION,
            )
        )


def _manifest_with_dimensions_in_two_models(  # noqa: D103
    first_model_dimension: PydanticDimension, second_model_dimension: PydanticDimension
) -> PydanticSemanticManifest:
    measure_name = "measure"
    return PydanticSemanticManifest(
        semantic_models=[
            semantic_model_with_guaranteed_meta(
                name="model_one",
                measures=[PydanticMeasure(name=measure_name, agg=AggregationType.SUM)],
                dimensions=[first_model_dimension],
            ),
            semantic_model_with_guaranteed_meta(name="model_two", dimensions=[second_model_dimension]),
        ],
        metrics=[
            metric_with_guaranteed_meta(
                name=measure_name,
                type=MetricType.SIMPLE,
                type_params=PydanticMetricTypeParams(measure=PydanticMetricInputMeasure(name=measure_name)),
            )
        ],
        project_configuration=EXAMPLE_PROJECT_CONFIGURATION,
    )


def test_different_dimension_sort_by_is_rejected() -> None:  # noqa: D103
    model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
    with pytest.raises(SemanticManifestValidationException, match=r"conflicting `sort_by` for dimension"):
        model_validator.checked_validations(
            _manifest_with_dimensions_in_two_models(
                PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, sort_by="rank"),
                PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, sort_by="other_rank"),
            )
        )


def test_different_dimension_label_by_is_rejected() -> None:  # noqa: D103
    model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
    with pytest.raises(SemanticManifestValidationException, match=r"conflicting `label_by` for dimension"):
        model_validator.checked_validations(
            _manifest_with_dimensions_in_two_models(
                PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, label_by="name"),
                PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, label_by="other_name"),
            )
        )


def test_conflict_is_found_against_declaration_after_an_unset_model() -> None:  # noqa: D103
    model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
    manifest = _manifest_with_dimensions_in_two_models(
        PydanticDimension(name="dim", type=DimensionType.CATEGORICAL),
        PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, label_by="name"),
    )
    manifest.semantic_models.append(
        semantic_model_with_guaranteed_meta(
            name="model_three",
            dimensions=[PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, label_by="other_name")],
        )
    )
    with pytest.raises(SemanticManifestValidationException, match=r"conflicting `label_by` for dimension"):
        model_validator.checked_validations(manifest)


@pytest.mark.parametrize(
    ("first_attributes", "second_attributes"),
    [
        ({"sort_by": "rank", "label_by": "name"}, {}),
        ({}, {"sort_by": "rank", "label_by": "name"}),
        ({"sort_by": "rank"}, {"label_by": "name"}),
        ({"label_by": "name"}, {"label_by": "name"}),
        ({"sort_by": "rank", "label_by": "name"}, {"sort_by": "rank", "label_by": "name"}),
    ],
)
def test_compatible_dimension_sort_by_and_label_by(  # noqa: D103
    first_attributes: Dict[str, str], second_attributes: Dict[str, str]
) -> None:
    model_validator = SemanticManifestValidator[PydanticSemanticManifest]([DimensionConsistencyRule()])
    model_validator.checked_validations(
        _manifest_with_dimensions_in_two_models(
            PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, **first_attributes),
            PydanticDimension(name="dim", type=DimensionType.CATEGORICAL, **second_attributes),
        )
    )
