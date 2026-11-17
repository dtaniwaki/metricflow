test_name: test_descendant_of_with_integer_value
test_filename: test_descendant_of_rendering.py
docstring:
  Check that an integer value is written as a number, not a string.
sql_engine: DuckDB
---
-- Constrain Output with WHERE
-- Select: ['employee__employee_key']
-- Write to DataTable
SELECT
  employee__employee_key
FROM (
  -- Read Elements From Semantic Model 'employees_source'
  -- Select: ['employee__employee_key']
  SELECT
    employee_id AS employee__employee_key
  FROM ***************************.dim_employees employees_source_src_36000
) subq_5
WHERE (employee__employee_key IN (7) OR employee__employee_key IN (WITH RECURSIVE descendant_of_tree(descendant_of_value) AS (SELECT (employee_id) FROM ***************************.dim_employees WHERE (manager_id) IN (7) UNION SELECT (employee_id) FROM ***************************.dim_employees JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value) SELECT descendant_of_value FROM descendant_of_tree))
GROUP BY
  employee__employee_key
