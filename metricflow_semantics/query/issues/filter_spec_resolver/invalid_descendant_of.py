from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from metricflow_semantics.errors.error_classes import InvalidDescendantOfError, InvalidQueryException
from metricflow_semantics.query.group_by_item.resolution_path import MetricFlowQueryResolutionPath
from metricflow_semantics.query.issues.issues_base import (
    MetricFlowQueryIssueType,
    MetricFlowQueryResolutionIssue,
)
from metricflow_semantics.query.resolver_inputs.base_resolver_inputs import MetricFlowQueryResolverInput
from typing_extensions import override


@dataclass(frozen=True)
class InvalidDescendantOfIssue(MetricFlowQueryResolutionIssue):
    """Describes an issue with a where filter that uses descendant_of on a dimension without a usable hierarchy."""

    object_builder_str: str
    failure_reason: str

    @staticmethod
    def from_parameters(  # noqa: D102
        object_builder_str: str,
        failure_reason: str,
        query_resolution_path: MetricFlowQueryResolutionPath,
    ) -> InvalidDescendantOfIssue:
        return InvalidDescendantOfIssue(
            issue_type=MetricFlowQueryIssueType.ERROR,
            parent_issues=(),
            query_resolution_path=query_resolution_path,
            object_builder_str=object_builder_str,
            failure_reason=failure_reason,
        )

    @property
    @override
    def exception_class(self) -> Type[InvalidQueryException]:
        return InvalidDescendantOfError

    @override
    def ui_description(self, associated_input: MetricFlowQueryResolverInput) -> str:
        return f"Can't use descendant_of on {self.object_builder_str} in a where filter. {self.failure_reason}"

    @override
    def with_path_prefix(self, path_prefix: MetricFlowQueryResolutionPath) -> InvalidDescendantOfIssue:
        return InvalidDescendantOfIssue(
            issue_type=self.issue_type,
            parent_issues=tuple(issue.with_path_prefix(path_prefix) for issue in self.parent_issues),
            query_resolution_path=self.query_resolution_path.with_path_prefix(path_prefix),
            object_builder_str=self.object_builder_str,
            failure_reason=self.failure_reason,
        )
