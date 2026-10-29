from __future__ import annotations

import dataclasses
from typing import Dict, Generic, List, Sequence

from metricflow_semantic_interfaces.protocols import SemanticManifestT, SemanticModel
from metricflow_semantic_interfaces.references import (
    DimensionReference,
    SemanticModelElementReference,
)
from metricflow_semantic_interfaces.validations.validator_helpers import (
    DimensionInvariants,
    FileContext,
    SemanticManifestValidationRule,
    SemanticModelElementContext,
    SemanticModelElementType,
    ValidationError,
    ValidationIssue,
    validate_safely,
)


class DimensionConsistencyRule(SemanticManifestValidationRule[SemanticManifestT], Generic[SemanticManifestT]):
    """Checks for consistent dimension properties in the semantic models in a model.

    * Dimensions with the same name should be of the same type.
    * Dimensions with the same name should be either all partitions or not.
    * Dimensions with the same name should not declare different `sort_by` values, and likewise for `label_by`.
      A dimension that declares neither is compatible with one that declares them.
    """

    @staticmethod
    @validate_safely(whats_being_done="running model validation ensuring dimension consistency")
    def validate_manifest(semantic_manifest: SemanticManifestT) -> Sequence[ValidationIssue]:  # noqa: D102
        dimension_to_invariant: Dict[DimensionReference, DimensionInvariants] = {}
        issues: List[ValidationIssue] = []

        for semantic_model in semantic_manifest.semantic_models:
            issues += DimensionConsistencyRule._validate_semantic_model(
                semantic_model=semantic_model, dimension_to_invariant=dimension_to_invariant, update_invariant_dict=True
            )

        return issues

    @staticmethod
    @validate_safely(
        whats_being_done="checking that the semantic model has dimensions consistent with the given invariants"
    )
    def _validate_semantic_model(
        semantic_model: SemanticModel,
        dimension_to_invariant: Dict[DimensionReference, DimensionInvariants],
        update_invariant_dict: bool,
    ) -> Sequence[ValidationIssue]:
        """Checks that the given semantic model has dimensions consistent with the given invariants.

        Args:
            semantic_model: the semantic model to check
            dimension_to_invariant: a dict from the dimension name to the properties it should have
            update_invariant_dict: whether to insert an entry into the dict if the given dimension name doesn't exist.
        Throws: MdoValidationError if there is an inconsistent dimension in the semantic model.
        """
        issues: List[ValidationIssue] = []

        for dimension in semantic_model.dimensions:
            dimension_invariant = dimension_to_invariant.get(dimension.reference)

            if dimension_invariant is None:
                if update_invariant_dict:
                    dimension_invariant = DimensionInvariants(
                        type=dimension.type,
                        is_partition=dimension.is_partition or False,
                        sort_by=dimension.sort_by,
                        label_by=dimension.label_by,
                    )
                    dimension_to_invariant[dimension.reference] = dimension_invariant
                    continue
                # TODO: Can't check for unknown dimensions easily as the name follows <id>__<name> format.
                # e.g. user__created_at
                continue

            # is_partition might not be specified in the configs, so default to False.
            is_partition = dimension.is_partition or False

            context = SemanticModelElementContext(
                file_context=FileContext.from_metadata(metadata=semantic_model.metadata),
                semantic_model_element=SemanticModelElementReference(
                    semantic_model_name=semantic_model.name, element_name=dimension.name
                ),
                element_type=SemanticModelElementType.DIMENSION,
            )

            if dimension_invariant.type != dimension.type:
                issues.append(
                    ValidationError(
                        context=context,
                        message=f"In semantic model `{semantic_model.name}`, type conflict for dimension "
                        f"`{dimension.name}` - already in model as type `{dimension_invariant.type}` but got "
                        f"`{dimension.type}`",
                    )
                )
            if dimension_invariant.is_partition != is_partition:
                issues.append(
                    ValidationError(
                        context=context,
                        message=f"In semantic model `{semantic_model.name}, conflicting is_partition attribute for "
                        f"dimension `{dimension.reference}` - already in model"
                        f" with is_partition as `{dimension_invariant.is_partition}` but got "
                        f"`{is_partition}``",
                    )
                )
            for attribute_name, invariant_value, value in (
                ("sort_by", dimension_invariant.sort_by, dimension.sort_by),
                ("label_by", dimension_invariant.label_by, dimension.label_by),
            ):
                if invariant_value is not None and value is not None and invariant_value != value:
                    issues.append(
                        ValidationError(
                            context=context,
                            message=f"In semantic model `{semantic_model.name}`, conflicting `{attribute_name}` for "
                            f"dimension `{dimension.name}` - already declared in another semantic model as "
                            f"`{invariant_value}` but got `{value}`",
                        )
                    )
            if update_invariant_dict:
                dimension_to_invariant[dimension.reference] = dataclasses.replace(
                    dimension_invariant,
                    sort_by=dimension_invariant.sort_by
                    if dimension_invariant.sort_by is not None
                    else dimension.sort_by,
                    label_by=(
                        dimension_invariant.label_by if dimension_invariant.label_by is not None else dimension.label_by
                    ),
                )

        return issues
