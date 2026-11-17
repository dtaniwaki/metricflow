from __future__ import annotations

from typing import Dict, Generic, List, Optional, Sequence

from metricflow_semantic_interfaces.protocols import Dimension, SemanticManifestT, SemanticModel
from metricflow_semantic_interfaces.references import SemanticModelElementReference
from metricflow_semantic_interfaces.type_enums import DimensionType
from metricflow_semantic_interfaces.validations.validator_helpers import (
    FileContext,
    SemanticManifestValidationRule,
    SemanticModelElementContext,
    SemanticModelElementType,
    ValidationError,
    ValidationIssue,
    validate_safely,
)


class DimensionValueColumnRule(SemanticManifestValidationRule[SemanticManifestT], Generic[SemanticManifestT]):
    """Checks that `sort_by` and `label_by` on a dimension refer to valid dimensions.

    * The referenced dimension must be an unqualified name of another dimension in the same semantic model.
    * Both the dimension and the referenced dimension must be categorical.
    """

    @staticmethod
    @validate_safely(whats_being_done="checking the sort_by and label_by of dimensions")
    def validate_manifest(semantic_manifest: SemanticManifestT) -> Sequence[ValidationIssue]:  # noqa: D102
        issues: List[ValidationIssue] = []
        for semantic_model in semantic_manifest.semantic_models:
            issues.extend(DimensionValueColumnRule._validate_semantic_model(semantic_model))
        return issues

    @staticmethod
    @validate_safely(whats_being_done="checking the sort_by and label_by of dimensions in a semantic model")
    def _validate_semantic_model(semantic_model: SemanticModel) -> Sequence[ValidationIssue]:
        issues: List[ValidationIssue] = []
        name_to_dimension: Dict[str, Dimension] = {dimension.name: dimension for dimension in semantic_model.dimensions}

        for dimension in semantic_model.dimensions:
            for attribute_name, referenced_name in (("sort_by", dimension.sort_by), ("label_by", dimension.label_by)):
                if referenced_name is None:
                    continue
                error_message = DimensionValueColumnRule._get_error_message(
                    dimension=dimension,
                    attribute_name=attribute_name,
                    referenced_name=referenced_name,
                    referenced_dimension=name_to_dimension.get(referenced_name),
                )
                if error_message is None:
                    continue
                issues.append(
                    ValidationError(
                        context=SemanticModelElementContext(
                            file_context=FileContext.from_metadata(metadata=semantic_model.metadata),
                            semantic_model_element=SemanticModelElementReference(
                                semantic_model_name=semantic_model.name, element_name=dimension.name
                            ),
                            element_type=SemanticModelElementType.DIMENSION,
                        ),
                        message=f"In semantic model `{semantic_model.name}`, dimension `{dimension.name}` "
                        f"has an invalid `{attribute_name}`: {error_message}",
                    )
                )

        return issues

    @staticmethod
    def _get_error_message(
        dimension: Dimension,
        attribute_name: str,
        referenced_name: str,
        referenced_dimension: Optional[Dimension],
    ) -> Optional[str]:
        if "__" in referenced_name:
            return (
                f"`{referenced_name}` must be the name of a dimension in the same semantic model, "
                f"without entity links."
            )
        if referenced_name == dimension.name:
            return f"`{referenced_name}` is the dimension itself."
        if referenced_dimension is None:
            return f"`{referenced_name}` is not a dimension in the same semantic model."
        if dimension.type is not DimensionType.CATEGORICAL:
            return f"`{attribute_name}` can only be set on a categorical dimension, but its type is `{dimension.type}`."
        if referenced_dimension.type is not DimensionType.CATEGORICAL:
            return (
                f"`{referenced_name}` must be a categorical dimension, but its type is `{referenced_dimension.type}`."
            )
        return None
