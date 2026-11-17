from __future__ import annotations

from typing import Sequence

from metricflow_semantics.model.semantics.linkable_element_set_base import AnnotatedSpec
from metricflow_semantics.specs.where_filter.descendant_of import DescendantOfSource


class RenderedSpecTracker:
    """Mutable object that is used to record the specs that were rendered in a where filter.

    This is useful for constructing a WhereFilterSpec as it includes a list of specs required by the filter.
    """

    def __init__(self) -> None:  # noqa: D107
        self._rendered_specs: list[AnnotatedSpec] = []
        self._descendant_of_sources: list[DescendantOfSource] = []

    def record_rendered_spec(self, spec: AnnotatedSpec) -> None:
        """Records a spec that was rendered in a where filter and can be retrieved later through rendered_specs()."""
        self._rendered_specs.append(spec)

    @property
    def rendered_specs(self) -> Sequence[AnnotatedSpec]:
        """Returns specs that were recorded by record_rendered_spec()."""
        return self._rendered_specs

    def record_descendant_of_source(self, source: DescendantOfSource) -> None:
        """Records the hierarchy of a `descendant_of` condition that was rendered in a where filter."""
        self._descendant_of_sources.append(source)

    @property
    def descendant_of_sources(self) -> Sequence[DescendantOfSource]:
        """Returns the sources that were recorded by record_descendant_of_source()."""
        return self._descendant_of_sources
