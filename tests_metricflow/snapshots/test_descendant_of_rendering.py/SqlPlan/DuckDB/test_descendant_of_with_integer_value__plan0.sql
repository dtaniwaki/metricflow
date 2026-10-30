test_name: test_descendant_of_with_integer_value
test_filename: test_descendant_of_rendering.py
docstring:
  Check that an integer value is written as a number, not a string.
sql_engine: DuckDB
---
-- Write to DataTable
SELECT
  subq_3.employee__employee_key
FROM (
  -- Select: ['employee__employee_key']
  SELECT
    subq_2.employee__employee_key
  FROM (
    -- Constrain Output with WHERE
    SELECT
      subq_1.employee__employee_key
    FROM (
      -- Select: ['employee__employee_key']
      SELECT
        subq_0.employee__employee_key
      FROM (
        -- Read Elements From Semantic Model 'employees_source'
        SELECT
          employees_source_src_36000.employee_id AS employee_key
          , employees_source_src_36000.manager_id AS manager_key
          , employees_source_src_36000.employee_name
          , employees_source_src_36000.employee_id AS employee__employee_key
          , employees_source_src_36000.manager_id AS employee__manager_key
          , employees_source_src_36000.employee_name AS employee__employee_name
          , employees_source_src_36000.employee_id AS employee
        FROM ***************************.dim_employees employees_source_src_36000
      ) subq_0
    ) subq_1
    WHERE (employee__employee_key IN (7) OR employee__employee_key IN (WITH RECURSIVE descendant_of_tree(descendant_of_value) AS (SELECT (employee_id) FROM ***************************.dim_employees WHERE (manager_id) IN (7) UNION SELECT (employee_id) FROM ***************************.dim_employees JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value) SELECT descendant_of_value FROM descendant_of_tree))
  ) subq_2
  GROUP BY
    subq_2.employee__employee_key
) subq_3
