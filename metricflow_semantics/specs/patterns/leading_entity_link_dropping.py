from __future__ import annotations

import logging
from itertools import islice
from typing import Iterator, Sequence

from metricflow_semantics.model.semantics.metric_lookup import MetricLookup
from metricflow_semantics.specs.patterns.spec_pattern import SpecPattern

logger = logging.getLogger(__name__)


def iter_patterns_dropping_leading_entity_links(patterns: Sequence[SpecPattern]) -> Iterator[Sequence[SpecPattern]]:
    """Yield the patterns as given, then with the first entity link removed from each, then the next one, and so on.

    The last entity link of a pattern is never removed. Patterns without a link to remove are kept as they are.
    """
    current_patterns = tuple(patterns)
    while True:
        yield current_patterns
        patterns_with_link_dropped = tuple(pattern.with_leading_entity_link_dropped() for pattern in current_patterns)
        if all(dropped is None for dropped in patterns_with_link_dropped):
            return
        current_patterns = tuple(
            current if dropped is None else dropped
            for current, dropped in zip(current_patterns, patterns_with_link_dropped)
        )


def iter_alias_patterns_for_no_metrics_query(
    patterns: Sequence[SpecPattern], metric_lookup: MetricLookup
) -> Iterator[Sequence[SpecPattern]]:
    """Yield the patterns with leading entity links removed, if the patterns are valid for a query with joins.

    Without metrics, there is no semantic model to start joins from, so `a__b__c` can be treated as an alias of
    `b__c`, which is also the name of the output column. Nothing is yielded if `a__b__c` could not be used in a query
    with metrics, and the patterns as given are not yielded.
    """
    if not metric_lookup.matches_distinct_values_query_items_allowing_joins(patterns):
        return
    yield from islice(iter_patterns_dropping_leading_entity_links(patterns), 1, None)
