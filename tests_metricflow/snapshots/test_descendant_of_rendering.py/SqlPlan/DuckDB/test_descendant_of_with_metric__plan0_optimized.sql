test_name: test_descendant_of_with_metric
test_filename: test_descendant_of_rendering.py
docstring:
  Check the SQL for a where filter that limits an employee to one employee and the ones reporting to them.
sql_engine: DuckDB
---
-- Constrain Output with WHERE
-- Select: ['__task_hours', 'employee__employee_key']
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Write to DataTable
SELECT
  employee__employee_key
  , SUM(task_hours) AS task_hours
FROM (
  -- Join Standard Outputs
  -- Select: ['__task_hours', 'employee__employee_key']
  SELECT
    employees_source_src_36000.employee_id AS employee__employee_key
    , tasks_source_src_36000.task_hours AS task_hours
  FROM ***************************.fct_tasks tasks_source_src_36000
  LEFT OUTER JOIN
    ***************************.dim_employees employees_source_src_36000
  ON
    tasks_source_src_36000.employee_id = employees_source_src_36000.employee_id
) subq_15
WHERE (employee__employee_key IN ('e2') OR employee__employee_key IN (WITH RECURSIVE descendant_of_tree(descendant_of_value) AS (SELECT (employee_id) FROM ***************************.dim_employees WHERE (manager_id) IN ('e2') UNION SELECT (employee_id) FROM ***************************.dim_employees JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value) SELECT descendant_of_value FROM descendant_of_tree))
GROUP BY
  employee__employee_key
