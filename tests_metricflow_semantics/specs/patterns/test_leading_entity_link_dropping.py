from __future__ import annotations

import logging
from typing import Sequence, cast

from metricflow_semantics.specs.patterns.entity_link_pattern import (
    EntityLinkPattern,
    ParameterSetField,
    SpecPatternParameterSet,
)
from metricflow_semantics.specs.patterns.leading_entity_link_dropping import (
    iter_patterns_dropping_leading_entity_links,
)
from metricflow_semantics.specs.patterns.no_group_by_metric import NoGroupByMetricPattern
from metricflow_semantics.specs.patterns.spec_pattern import SpecPattern

from metricflow_semantic_interfaces.references import EntityReference

logger = logging.getLogger(__name__)


def _pattern(*entity_link_names: str) -> EntityLinkPattern:
    return EntityLinkPattern(
        parameter_set=SpecPatternParameterSet.from_parameters(
            fields_to_compare=(ParameterSetField.ELEMENT_NAME, ParameterSetField.ENTITY_LINKS),
            element_name="element",
            entity_links=tuple(EntityReference(name) for name in entity_link_names),
        )
    )


def _entity_link_names(pattern: SpecPattern) -> Sequence[str]:
    entity_links = cast(EntityLinkPattern, pattern).parameter_set.entity_links
    assert entity_links is not None
    return tuple(entity_link.element_name for entity_link in entity_links)


def test_links_are_dropped_one_at_a_time_and_last_link_is_kept() -> None:
    """Each step removes one leading link, and the last link is never removed."""
    steps = [
        tuple(_entity_link_names(pattern) for pattern in patterns)
        for patterns in iter_patterns_dropping_leading_entity_links((_pattern("a", "b", "c"),))
    ]
    assert steps == [(("a", "b", "c"),), (("b", "c"),), (("c",),)]


def test_pattern_with_one_link_is_yielded_once() -> None:
    """A pattern with a single link has nothing to drop."""
    original = _pattern("a")
    assert list(iter_patterns_dropping_leading_entity_links((original,))) == [(original,)]


def test_patterns_that_can_not_drop_are_kept_while_others_drop() -> None:
    """A pattern that has no link to drop stays in every step."""
    other_pattern = NoGroupByMetricPattern()
    steps = list(iter_patterns_dropping_leading_entity_links((_pattern("a", "b", "c"), other_pattern)))
    assert [_entity_link_names(patterns[0]) for patterns in steps] == [("a", "b", "c"), ("b", "c"), ("c",)]
    assert all(patterns[1] is other_pattern for patterns in steps)


def test_patterns_with_different_link_counts_stop_when_all_are_at_the_last_link() -> None:
    """The steps continue until no pattern can drop, and a pattern at its last link stays."""
    steps = list(iter_patterns_dropping_leading_entity_links((_pattern("a", "b", "c"), _pattern("x", "y"))))
    assert [tuple(_entity_link_names(pattern) for pattern in patterns) for patterns in steps] == [
        (("a", "b", "c"), ("x", "y")),
        (("b", "c"), ("y",)),
        (("c",), ("y",)),
    ]
