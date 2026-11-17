from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Sequence, Set

from metricflow_semantics.specs.where_filter.descendant_of import DescendantOfSource

from metricflow_semantic_interfaces.naming.keywords import DUNDER
from metricflow_semantic_interfaces.protocols import SemanticModel
from metricflow_semantic_interfaces.type_enums import EntityType

logger = logging.getLogger(__name__)

_LINKABLE_ENTITY_TYPES = (EntityType.PRIMARY, EntityType.UNIQUE, EntityType.NATURAL)


@dataclass(frozen=True)
class DescendantOfSourceLookupResult:
    """Either the source for a `descendant_of` filter, or the reason there is none. Exactly one is set."""

    # Set when the hierarchy was found.
    source: Optional[DescendantOfSource]
    # Set when it was not, and says why.
    failure_reason: Optional[str]

    @staticmethod
    def for_source(source: DescendantOfSource) -> DescendantOfSourceLookupResult:  # noqa: D102
        return DescendantOfSourceLookupResult(source=source, failure_reason=None)

    @staticmethod
    def for_failure(failure_reason: str) -> DescendantOfSourceLookupResult:  # noqa: D102
        return DescendantOfSourceLookupResult(source=None, failure_reason=failure_reason)


class HierarchyLookup:
    """Finds the self-referencing levels declared in the dimension hierarchies of semantic models."""

    def __init__(self, semantic_models: Sequence[SemanticModel]) -> None:  # noqa: D107
        self._semantic_model_by_name = {semantic_model.name: semantic_model for semantic_model in semantic_models}

    def find_descendant_of_source(
        self, semantic_model_names: Sequence[str], dimension_name: str
    ) -> DescendantOfSourceLookupResult:
        """Return where to read the hierarchy of the dimension from, given the semantic models that define it."""
        sources: Set[DescendantOfSource] = set()
        failure_reasons = []
        for semantic_model_name in semantic_model_names:
            result = self._find_in_semantic_model(self._semantic_model_by_name[semantic_model_name], dimension_name)
            if result.source is not None:
                sources.add(result.source)
            elif result.failure_reason is not None:
                failure_reasons.append(result.failure_reason)

        if len(sources) == 1 and len(failure_reasons) == 0:
            return DescendantOfSourceLookupResult.for_source(next(iter(sources)))
        if len(sources) > 1:
            return DescendantOfSourceLookupResult.for_failure(
                f"The dimension {dimension_name!r} has different hierarchies in {sorted(semantic_model_names)}."
            )
        if failure_reasons:
            return DescendantOfSourceLookupResult.for_failure(" ".join(failure_reasons))
        return DescendantOfSourceLookupResult.for_failure(
            f"The dimension {dimension_name!r} is not defined in a semantic model."
        )

    def _find_in_semantic_model(
        self, semantic_model: SemanticModel, dimension_name: str
    ) -> DescendantOfSourceLookupResult:
        parent_names: Set[Optional[str]] = set()
        declared_through_another_model = False
        for hierarchy in semantic_model.hierarchies:
            for level in hierarchy.levels:
                local_name = self._local_dimension_name(semantic_model, level.dimension)
                if local_name is None:
                    declared_through_another_model |= level.dimension.split(DUNDER)[-1] == dimension_name
                elif local_name == dimension_name and level.parent is not None:
                    parent_names.add(self._local_dimension_name(semantic_model, level.parent))

        model_name = semantic_model.name
        if len(parent_names) == 0:
            if declared_through_another_model:
                return DescendantOfSourceLookupResult.for_failure(
                    f"The hierarchy of {dimension_name!r} in the semantic model {model_name!r} is declared with a "
                    f"dimension that is qualified by another semantic model, which descendant_of does not support."
                )
            return DescendantOfSourceLookupResult.for_failure(
                f"The dimension {dimension_name!r} is not a level with a parent in any hierarchy of the semantic "
                f"model {model_name!r}. Declare it as a level with a `parent` to use descendant_of."
            )

        parent_name = next(iter(parent_names))
        if len(parent_names) != 1 or parent_name is None:
            return DescendantOfSourceLookupResult.for_failure(
                f"The dimension {dimension_name!r} has more than one parent, or a parent that is not a dimension of "
                f"the semantic model {model_name!r}."
            )

        return DescendantOfSourceLookupResult.for_source(
            DescendantOfSource(
                relation_sql=semantic_model.node_relation.relation_name,
                key_expr=self._dimension_expr(semantic_model, dimension_name),
                parent_expr=self._dimension_expr(semantic_model, parent_name),
            )
        )

    @staticmethod
    def _dimension_expr(semantic_model: SemanticModel, dimension_name: str) -> str:
        for dimension in semantic_model.dimensions:
            if dimension.name == dimension_name:
                return dimension.expr or dimension.name
        raise RuntimeError(f"Dimension {dimension_name!r} is not in the semantic model {semantic_model.name!r}.")

    @staticmethod
    def _local_dimension_name(semantic_model: SemanticModel, name: str) -> Optional[str]:
        """Return the dimension name if `name` refers to a dimension of the semantic model itself, else None.

        A dimension may be written bare (`city`) or qualified by an entity that the semantic model exposes
        (`store__city`).
        """
        dimension_names = {dimension.name for dimension in semantic_model.dimensions}
        parts = name.split(DUNDER)
        if len(parts) == 1:
            return name if name in dimension_names else None
        if len(parts) == 2 and parts[1] in dimension_names:
            exposes_entity = semantic_model.primary_entity == parts[0] or any(
                entity.name == parts[0] and entity.type in _LINKABLE_ENTITY_TYPES for entity in semantic_model.entities
            )
            return parts[1] if exposes_entity else None
        return None
