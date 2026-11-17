from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from metricflow_semantics.errors.error_classes import InvalidQueryException
from metricflow_semantics.model.semantics.dimension_lookup import DimensionLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dimension_spec import DimensionSpec
from metricflow_semantics.specs.instance_spec import InstanceSpec
from metricflow_semantics.specs.order_by_spec import OrderBySpec
from metricflow_semantics.specs.query_spec import InputSpecOrder, MetricFlowQuerySpec

from metricflow_semantic_interfaces.references import DimensionReference

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DimensionValueAttributeSpecSet:
    """The specs of the dimensions declared by `label_by` and `sort_by` for a dimension."""

    # The queried dimension that declares `label_by` and `sort_by`.
    dimension_spec: DimensionSpec
    # The dimension holding the display name of the value, if `label_by` is declared.
    label_spec: Optional[DimensionSpec]
    # The dimension holding the sort key of the value, if `sort_by` is declared.
    sort_spec: Optional[DimensionSpec]

    @property
    def attribute_specs(self) -> Tuple[DimensionSpec, ...]:
        """The specs that are set, label first."""
        return tuple(spec for spec in (self.label_spec, self.sort_spec) if spec is not None)

    @staticmethod
    def for_dimension_spec(
        dimension_spec: DimensionSpec, dimension_lookup: DimensionLookup, query_parser: MetricFlowQueryParser
    ) -> DimensionValueAttributeSpecSet:
        """Resolve the specs, which have the same entity links as the given spec.

        A declared dimension is only used if it can be queried with the same entity links as the given spec. Otherwise,
        the given spec is reached through a semantic model that does not declare it, and it has no label or sort key.
        """
        invariant = dimension_lookup.get_invariant(dimension_spec.reference)

        def _spec_for(reference: Optional[DimensionReference]) -> Optional[DimensionSpec]:
            if reference is None:
                return None
            spec = DimensionSpec(element_name=reference.element_name, entity_links=dimension_spec.entity_links)
            try:
                query_parser.parse_and_validate_query(group_by_names=(spec.dunder_name,))
            except InvalidQueryException:
                return None
            return spec

        return DimensionValueAttributeSpecSet(
            dimension_spec=dimension_spec,
            label_spec=_spec_for(invariant.label_by),
            sort_spec=_spec_for(invariant.sort_by),
        )


@dataclass(frozen=True)
class DimensionValueQuerySpec:
    """A query spec extended with the `label_by` and `sort_by` dimensions of the queried dimensions."""

    query_spec: MetricFlowQuerySpec
    # One item for each queried dimension, in the order of the query.
    attribute_spec_sets: Tuple[DimensionValueAttributeSpecSet, ...]


def add_dimension_value_attributes(
    query_spec: MetricFlowQuerySpec, dimension_lookup: DimensionLookup, query_parser: MetricFlowQueryParser
) -> DimensionValueQuerySpec:
    """Add the `label_by` and `sort_by` dimensions of the queried dimensions as group-by items.

    Each added item is placed right after the dimension that declares it. If the query has no order-by, the result is
    ordered by `sort_by` for the dimensions that declare it, with the dimension itself breaking ties.
    """
    already_queried_specs = {
        spec.with_alias(None) for spec in query_spec.dimension_specs + query_spec.time_dimension_specs
    }
    attribute_spec_sets = tuple(
        DimensionValueAttributeSpecSet.for_dimension_spec(dimension_spec, dimension_lookup, query_parser)
        for dimension_spec in query_spec.dimension_specs
    )
    spec_set_by_dimension_spec: Dict[InstanceSpec, DimensionValueAttributeSpecSet] = {
        spec_set.dimension_spec: spec_set for spec_set in attribute_spec_sets
    }

    added_specs: List[DimensionSpec] = []
    input_group_by_item_specs: List[InstanceSpec] = []
    for input_spec in query_spec.input_spec_order.group_by_item_specs:
        input_group_by_item_specs.append(input_spec)
        spec_set = spec_set_by_dimension_spec.get(input_spec)
        if spec_set is None:
            continue
        for attribute_spec in spec_set.attribute_specs:
            if attribute_spec in already_queried_specs or attribute_spec in added_specs:
                continue
            added_specs.append(attribute_spec)
            input_group_by_item_specs.append(attribute_spec)

    order_by_specs = query_spec.order_by_specs
    if len(order_by_specs) == 0:
        order_by_specs = tuple(
            order_by_spec
            for spec_set in attribute_spec_sets
            if spec_set.sort_spec is not None
            for order_by_spec in (
                OrderBySpec(instance_spec=spec_set.sort_spec, descending=False),
                OrderBySpec(instance_spec=spec_set.dimension_spec.with_alias(None), descending=False),
            )
        )

    return DimensionValueQuerySpec(
        query_spec=dataclasses.replace(
            query_spec,
            dimension_specs=query_spec.dimension_specs + tuple(added_specs),
            order_by_specs=order_by_specs,
            input_spec_order=InputSpecOrder(
                group_by_item_specs=tuple(input_group_by_item_specs),
                metric_specs=query_spec.input_spec_order.metric_specs,
            ),
        ),
        attribute_spec_sets=attribute_spec_sets,
    )
