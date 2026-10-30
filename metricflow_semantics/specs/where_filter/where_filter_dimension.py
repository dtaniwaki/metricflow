from __future__ import annotations

import logging
from typing import Optional, Sequence, Union

from metricflow_semantics.errors.error_classes import InvalidQuerySyntax
from metricflow_semantics.naming.linkable_spec_name import StructuredLinkableSpecName
from metricflow_semantics.query.group_by_item.filter_spec_resolution.filter_location import WhereFilterLocation
from metricflow_semantics.query.group_by_item.filter_spec_resolution.filter_spec_lookup import (
    FilterSpecResolutionLookUp,
    ResolvedSpecLookUpKey,
)
from metricflow_semantics.specs.column_assoc import ColumnAssociationResolver
from metricflow_semantics.specs.rendered_spec_tracker import RenderedSpecTracker
from metricflow_semantics.specs.where_filter.descendant_of import render_descendant_of_sql
from typing_extensions import override

from metricflow_semantic_interfaces.call_parameter_sets import (
    DimensionCallParameterSet,
    TimeDimensionCallParameterSet,
)
from metricflow_semantic_interfaces.descendant_of_value import DescendantOfValue
from metricflow_semantic_interfaces.protocols.protocol_hint import ProtocolHint
from metricflow_semantic_interfaces.protocols.query_interface import (
    QueryInterfaceDimension,
    QueryInterfaceDimensionFactory,
)
from metricflow_semantic_interfaces.references import DimensionReference, EntityReference, TimeDimensionReference
from metricflow_semantic_interfaces.type_enums.date_part import DatePart

logger = logging.getLogger(__name__)


class WhereFilterDimension(ProtocolHint[QueryInterfaceDimension]):
    """A dimension that is passed in through the where filter parameter."""

    @override
    def _implements_protocol(self) -> QueryInterfaceDimension:
        return self

    def __init__(  # noqa
        self,
        column_association_resolver: ColumnAssociationResolver,
        resolved_spec_lookup: FilterSpecResolutionLookUp,
        where_filter_location: WhereFilterLocation,
        rendered_spec_tracker: RenderedSpecTracker,
        element_name: str,
        entity_links: Sequence[EntityReference],
        time_granularity_name: Optional[str] = None,
        date_part: Optional[DatePart] = None,
        descendant_of_value: Optional[DescendantOfValue] = None,
    ) -> None:
        self._column_association_resolver = column_association_resolver
        self._resolved_spec_lookup = resolved_spec_lookup
        self._where_filter_location = where_filter_location
        self._rendered_spec_tracker = rendered_spec_tracker
        self._element_name = element_name
        self._entity_links = tuple(entity_links)
        self._time_granularity_name = time_granularity_name
        self._date_part = date_part
        self._descendant_of_value = descendant_of_value

    def grain(self, time_granularity_name: str) -> QueryInterfaceDimension:
        """The time granularity."""
        return WhereFilterDimension(
            column_association_resolver=self._column_association_resolver,
            resolved_spec_lookup=self._resolved_spec_lookup,
            where_filter_location=self._where_filter_location,
            rendered_spec_tracker=self._rendered_spec_tracker,
            element_name=self._element_name,
            entity_links=self._entity_links,
            time_granularity_name=time_granularity_name.lower(),
            date_part=self._date_part,
            descendant_of_value=self._descendant_of_value,
        )

    def date_part(self, date_part_name: str) -> QueryInterfaceDimension:
        """The date_part requested to extract."""
        return WhereFilterDimension(
            column_association_resolver=self._column_association_resolver,
            resolved_spec_lookup=self._resolved_spec_lookup,
            where_filter_location=self._where_filter_location,
            rendered_spec_tracker=self._rendered_spec_tracker,
            element_name=self._element_name,
            entity_links=self._entity_links,
            time_granularity_name=self._time_granularity_name,
            date_part=DatePart(date_part_name.lower()),
            descendant_of_value=self._descendant_of_value,
        )

    def descendant_of(self, value: Union[str, int]) -> QueryInterfaceDimension:
        """Filter to the given value and the values below it in the hierarchy of the dimension."""
        return WhereFilterDimension(
            column_association_resolver=self._column_association_resolver,
            resolved_spec_lookup=self._resolved_spec_lookup,
            where_filter_location=self._where_filter_location,
            rendered_spec_tracker=self._rendered_spec_tracker,
            element_name=self._element_name,
            entity_links=self._entity_links,
            time_granularity_name=self._time_granularity_name,
            date_part=self._date_part,
            descendant_of_value=DescendantOfValue.create(value),
        )

    def descending(self, _is_descending: bool) -> QueryInterfaceDimension:
        """Set the sort order for order-by."""
        raise InvalidQuerySyntax("descending is invalid in the where parameter")

    def __str__(self) -> str:
        """Returns the column name.

        Important in the Jinja sandbox.
        """
        call_parameter_set: Union[TimeDimensionCallParameterSet, DimensionCallParameterSet]
        if self._time_granularity_name is not None or self._date_part is not None:
            call_parameter_set = TimeDimensionCallParameterSet(
                entity_path=self._entity_links,
                time_dimension_reference=TimeDimensionReference(self._element_name),
                time_granularity_name=self._time_granularity_name,
                date_part=self._date_part,
            )
        else:
            call_parameter_set = DimensionCallParameterSet(
                entity_path=self._entity_links,
                dimension_reference=DimensionReference(self._element_name),
                descendant_of_value=self._descendant_of_value,
            )

        resolved_spec_key = ResolvedSpecLookUpKey(
            filter_location=self._where_filter_location,
            call_parameter_set=call_parameter_set,
        )

        resolved_spec = self._resolved_spec_lookup.checked_resolved_spec(resolved_spec_key)
        self._rendered_spec_tracker.record_rendered_spec(resolved_spec)
        column_association = self._column_association_resolver.resolve_spec(resolved_spec.spec)

        if self._descendant_of_value is None:
            return column_association.column_name

        descendant_of_source = self._resolved_spec_lookup.checked_descendant_of_source(resolved_spec_key)
        self._rendered_spec_tracker.record_descendant_of_source(descendant_of_source)
        return render_descendant_of_sql(
            column_name=column_association.column_name,
            source=descendant_of_source,
            value_sql=self._descendant_of_value.sql,
        )


class WhereFilterDimensionFactory(ProtocolHint[QueryInterfaceDimensionFactory]):
    """Creates a WhereFilterDimension.

    Each call to `create` adds a WhereFilterDimension to created.
    """

    @override
    def _implements_protocol(self) -> QueryInterfaceDimensionFactory:
        return self

    def __init__(  # noqa
        self,
        column_association_resolver: ColumnAssociationResolver,
        spec_resolution_lookup: FilterSpecResolutionLookUp,
        where_filter_location: WhereFilterLocation,
        rendered_spec_tracker: RenderedSpecTracker,
        custom_granularity_names: Sequence[str],
    ):
        self._column_association_resolver = column_association_resolver
        self._resolved_spec_lookup = spec_resolution_lookup
        self._where_filter_location = where_filter_location
        self._rendered_spec_tracker = rendered_spec_tracker
        self._custom_granularity_names = custom_granularity_names

    def create(self, name: str, entity_path: Sequence[str] = ()) -> WhereFilterDimension:
        """Create a WhereFilterDimension."""
        structured_name = StructuredLinkableSpecName.from_name(
            name.lower(), custom_granularity_names=self._custom_granularity_names
        )

        return WhereFilterDimension(
            column_association_resolver=self._column_association_resolver,
            resolved_spec_lookup=self._resolved_spec_lookup,
            where_filter_location=self._where_filter_location,
            rendered_spec_tracker=self._rendered_spec_tracker,
            element_name=structured_name.element_name,
            entity_links=tuple(EntityReference(entity_link_name.lower()) for entity_link_name in entity_path)
            + structured_name.entity_links,
        )
