# Custom Build

Base: v0.213.0
Date: 2026-10-31

## Included PRs

- https://github.com/dbt-labs/metricflow/pull/2143 — Add dimension hierarchies to semantic models
- https://github.com/dbt-labs/metricflow/pull/2150 — Add exclude_dimensions to ratio and derived metric inputs
- https://github.com/dtaniwaki/metricflow/pull/1 — Add MetricLookup.get_aggregation_time_dimension_specs_by_simple_metric
- https://github.com/dtaniwaki/metricflow/pull/2 — Resolve dimension names joined through entity links in queries without metrics
- https://github.com/dtaniwaki/metricflow/pull/3 — Add sort_by and label_by to dimensions
- https://github.com/dtaniwaki/metricflow/pull/4 — Add descendant_of to dimensions in where filters
- https://github.com/dtaniwaki/metricflow/pull/5 — Allow descendant_of on Athena and Trino

## Conflict Resolutions

- `metricflow/converters/converter_issues.py`: PR 3 and the hierarchies PR each added a `ConverterIssueType` member; both are kept (rerere, resolved by hand the first time).
- `tests_metricflow_semantic_interfaces/osi/test_msi_to_osi.py`: both PRs added a test at the same place; both are kept (rerere).
- `metricflow_semantics/errors/error_classes.py`: PR 2150 and PR 4 each added error classes after `InvalidQueryException`; all three (`InvalidExcludedFilterError`, `UnmatchedExcludeDimensionsError`, `InvalidDescendantOfError`) are kept, each with its own body (rerere, resolved by hand the first time).
- `tests_metricflow/fixtures/manifest_fixtures.py`: PR 3 and PR 4 each used id number block 13 for their test manifest; the hierarchy manifest of PR 4 moves to block 14 (rerere). Each PR on its own is unaffected.

PR 5 is based on PR 4 and merges without conflicts.

## Verification

Run on the merged result, one test tree at a time:

- `tests_metricflow_semantics`: 351 passed, 2 skipped.
- `tests_metricflow_semantic_interfaces`: 554 passed, 2 skipped.
- `tests_metricflow`: query_rendering 230 passed, 3 skipped; plan_conversion 60 passed; sql 126 passed, 1 skipped; metric_evaluation 157 passed; dataflow 91 passed; integration 636 passed, 2 skipped; engine 18 passed.

PR 2150 now raises dedicated error classes for its refusals, so callers can tell them apart without matching message text. PR 2150 and PR 4 are single commits and PR 5 sits on the squashed PR 4; the rerere resolutions above still applied.

PR 2150 also compares time keys with a null-safe equality, rejects inputs that share an output name but have different exclusions, and drops a compound NOT that only references excluded dimensions. The rerere resolutions above applied again without manual changes.
