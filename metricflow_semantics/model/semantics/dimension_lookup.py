from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from metricflow_semantics.model.semantics.semantic_model_helper import SemanticModelHelper
from metricflow_semantics.naming.linkable_spec_name import StructuredLinkableSpecName
from metricflow_semantics.toolkit.mf_logging.lazy_formattable import LazyFormat

from metricflow_semantic_interfaces.protocols import Dimension, SemanticModel
from metricflow_semantic_interfaces.references import DimensionReference
from metricflow_semantic_interfaces.type_enums import DimensionType


@dataclass(frozen=True)
class DimensionInvariant:
    """For a given manifest, all defined dimensions with the same name should have these same properties.

    `sort_by` and `label_by` are the declarations of the semantic models that declare them. Dimensions that do not
    declare them are compatible with the ones that do.
    """

    dimension_type: DimensionType
    is_partition: bool
    # The dimension in the same semantic model that defines the sort order of the values, if declared.
    sort_by: Optional[DimensionReference] = None
    # The dimension in the same semantic model that holds the display names of the values, if declared.
    label_by: Optional[DimensionReference] = None


class DimensionLookup:
    """Looks up properties related to dimensions."""

    def __init__(self, semantic_models: Sequence[SemanticModel]) -> None:  # noqa: D107
        self._dimension_reference_to_invariant: Dict[DimensionReference, DimensionInvariant] = {}
        self.dimensions_by_dunder_name: Dict[str, Dimension] = {}
        for semantic_model in semantic_models:
            for dimension in semantic_model.dimensions:
                invariant = DimensionInvariant(
                    dimension_type=dimension.type,
                    is_partition=dimension.is_partition,
                    sort_by=DimensionReference(dimension.sort_by) if dimension.sort_by is not None else None,
                    label_by=DimensionReference(dimension.label_by) if dimension.label_by is not None else None,
                )
                dimension_reference = dimension.reference
                existing_invariant = self._dimension_reference_to_invariant.get(dimension_reference)
                if existing_invariant is not None:
                    invariant = DimensionLookup._merge_invariants(
                        existing_invariant=existing_invariant,
                        invariant=invariant,
                        dimension_reference=dimension_reference,
                        semantic_model=semantic_model,
                    )

                self._dimension_reference_to_invariant[dimension_reference] = invariant
                primary_entity = SemanticModelHelper.resolved_primary_entity(semantic_model)
                structured_name = StructuredLinkableSpecName(
                    entity_link_names=(primary_entity.element_name,), element_name=dimension.name
                )
                self.dimensions_by_dunder_name[structured_name.dunder_name] = dimension

    @staticmethod
    def _merge_invariants(
        existing_invariant: DimensionInvariant,
        invariant: DimensionInvariant,
        dimension_reference: DimensionReference,
        semantic_model: SemanticModel,
    ) -> DimensionInvariant:
        """Merge two invariants, taking `sort_by` and `label_by` from whichever declares them.

        Raises:
            ValueError: if the type or partition flag differ, or if both declare different `sort_by` or `label_by`.
        """
        sort_by = existing_invariant.sort_by if existing_invariant.sort_by is not None else invariant.sort_by
        label_by = existing_invariant.label_by if existing_invariant.label_by is not None else invariant.label_by
        merged_invariant = DimensionInvariant(
            dimension_type=invariant.dimension_type,
            is_partition=invariant.is_partition,
            sort_by=sort_by,
            label_by=label_by,
        )
        both_declare_different_sort_by = (
            existing_invariant.sort_by is not None
            and invariant.sort_by is not None
            and existing_invariant.sort_by != invariant.sort_by
        )
        both_declare_different_label_by = (
            existing_invariant.label_by is not None
            and invariant.label_by is not None
            and existing_invariant.label_by != invariant.label_by
        )
        if (
            existing_invariant.dimension_type != invariant.dimension_type
            or existing_invariant.is_partition != invariant.is_partition
            or both_declare_different_sort_by
            or both_declare_different_label_by
        ):
            raise ValueError(
                LazyFormat(
                    "Dimensions with the same name have been defined with conflicting values that "
                    "should have been the same in a given semantic manifest. This should have been caught "
                    "during validation.",
                    dimension_reference=dimension_reference,
                    existing_invariant=existing_invariant,
                    conflicting_invariant=invariant,
                    semantic_model_reference=semantic_model.reference,
                )
            )
        return merged_invariant

    def get_invariant(self, dimension_reference: DimensionReference) -> DimensionInvariant:
        """Get invariants for the given dimension in the semantic manifest."""
        # dimension_reference might be a TimeDimensionReference, so change types.
        dimension_reference = DimensionReference(element_name=dimension_reference.element_name)
        invariant = self._dimension_reference_to_invariant[dimension_reference]
        if invariant is None:
            raise ValueError(
                LazyFormat(
                    "Unknown dimension reference",
                    dimension_reference=dimension_reference,
                    known_dimension_references=list(self._dimension_reference_to_invariant.keys()),
                )
            )

        return invariant
