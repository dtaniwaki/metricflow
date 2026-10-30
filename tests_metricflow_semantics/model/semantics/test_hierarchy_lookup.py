from __future__ import annotations

import textwrap

import pytest
from metricflow_semantics.model.semantics.hierarchy_lookup import HierarchyLookup
from metricflow_semantics.specs.where_filter.descendant_of import DescendantOfSource
from metricflow_semantics.sql.sql_table import SqlTable

from metricflow_semantic_interfaces.parsing.dir_to_model import parse_yaml_files_to_semantic_manifest
from metricflow_semantic_interfaces.parsing.objects import YamlConfigFile
from tests_metricflow_semantic_interfaces.example_project_configuration import (
    EXAMPLE_PROJECT_CONFIGURATION_YAML_CONFIG_FILE,
)

_SEMANTIC_MODELS_YAML = textwrap.dedent(
    """\
    semantic_model:
      name: employees
      node_relation:
        alias: dim_employees
        schema_name: some_schema
      entities:
        - name: employee
          type: primary
          expr: employee_id
      dimensions:
        - name: employee_key
          type: categorical
          expr: "UPPER(employee_id)"
        - name: manager_key
          type: categorical
          expr: manager_id
        - name: other_manager_key
          type: categorical
        - name: country
          type: categorical
        - name: store_region
          type: categorical
      hierarchies:
        - name: reporting_line
          levels:
            - dimension: employee__employee_key
              parent: manager_key
        - name: geography
          levels: [country]
        - name: ambiguous_line
          levels:
            - dimension: other_manager_key
              parent: manager_key
        - name: ambiguous_line_again
          levels:
            - dimension: other_manager_key
              parent: country
        - name: through_other_model
          levels:
            - dimension: store__store_region
              parent: store__store_parent
    ---
    semantic_model:
      name: employees_in_database
      node_relation:
        alias: dim_employees
        schema_name: some_schema
        database: some_database
      entities:
        - name: employee
          type: primary
          expr: employee_id
      dimensions:
        - name: employee_key
          type: categorical
        - name: manager_key
          type: categorical
      hierarchies:
        - name: reporting_line
          levels:
            - dimension: employee_key
              parent: manager_key
    ---
    semantic_model:
      name: employees_copy
      node_relation:
        alias: dim_employees_copy
        schema_name: some_schema
      entities:
        - name: employee
          type: unique
          expr: employee_id
      dimensions:
        - name: employee_key
          type: categorical
        - name: manager_key
          type: categorical
      hierarchies:
        - name: reporting_line
          levels:
            - dimension: employee_key
              parent: manager_key
    """
)


@pytest.fixture(scope="module")
def hierarchy_lookup() -> HierarchyLookup:  # noqa: D103
    build_result = parse_yaml_files_to_semantic_manifest(
        files=[
            YamlConfigFile(filepath="test_dir/inline_for_test", contents=_SEMANTIC_MODELS_YAML),
            EXAMPLE_PROJECT_CONFIGURATION_YAML_CONFIG_FILE,
        ]
    )
    return HierarchyLookup(build_result.semantic_manifest.semantic_models)


def test_source_for_a_level_with_a_parent(hierarchy_lookup: HierarchyLookup) -> None:
    """The key and the parent are read with the dimension expressions, from the relation of the semantic model."""
    result = hierarchy_lookup.find_descendant_of_source(("employees",), "employee_key")

    assert result.failure_reason is None
    assert result.source == DescendantOfSource(
        relation_sql="some_schema.dim_employees", key_expr="UPPER(employee_id)", parent_expr="manager_id"
    )


def test_semantic_models_that_define_a_level_differently_conflict(
    hierarchy_lookup: HierarchyLookup,
) -> None:
    """Semantic models that define the same level in different ways give no single source."""
    result = hierarchy_lookup.find_descendant_of_source(("employees", "employees_copy"), "employee_key")

    assert result.source is None
    assert result.failure_reason is not None
    assert "different hierarchies" in result.failure_reason


@pytest.mark.parametrize(
    "dimension_name,expected_message",
    [
        ("country", "not a level with a parent"),
        ("manager_key", "not a level with a parent"),
        ("other_manager_key", "more than one parent"),
        ("store_region", "another semantic model"),
    ],
)
def test_no_source_for_a_dimension_that_cannot_be_descended(  # noqa: D103
    hierarchy_lookup: HierarchyLookup, dimension_name: str, expected_message: str
) -> None:
    result = hierarchy_lookup.find_descendant_of_source(("employees",), dimension_name)

    assert result.source is None
    assert result.failure_reason is not None
    assert expected_message in result.failure_reason


@pytest.mark.parametrize("semantic_model_name", ["employees", "employees_in_database"])
def test_relation_is_written_like_the_table_of_the_source_node(  # noqa: D103
    hierarchy_lookup: HierarchyLookup, semantic_model_name: str
) -> None:
    result = hierarchy_lookup.find_descendant_of_source((semantic_model_name,), "employee_key")

    assert result.source is not None
    expected_relation_sql = {
        "employees": "some_schema.dim_employees",
        "employees_in_database": "some_database.some_schema.dim_employees",
    }[semantic_model_name]
    assert result.source.relation_sql == expected_relation_sql
    assert SqlTable.from_string(expected_relation_sql).sql == expected_relation_sql
