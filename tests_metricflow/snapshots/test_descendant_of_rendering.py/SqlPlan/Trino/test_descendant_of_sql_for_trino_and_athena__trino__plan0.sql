test_name: test_descendant_of_sql_for_trino_and_athena[trino]
test_filename: test_descendant_of_rendering.py
docstring:
  Check the SQL that the Trino and Athena renderers write, as snapshots of engines the tests don't run.
sql_engine: Trino
---
-- Constrain Output with WHERE
-- Select: ['__task_hours', 'employee__employee_key', 'metric_time__day']
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Order By ['employee__employee_key'] Limit 5
-- Write to DataTable
SELECT
  metric_time__day
  , employee__employee_key
  , SUM(task_hours) AS task_hours
FROM (
  -- Join Standard Outputs
  -- Select: ['__task_hours', 'employee__employee_key', 'metric_time__day']
  SELECT
    subq_3.metric_time__day AS metric_time__day
    , employees_source_src_36000.employee_id AS employee__employee_key
    , subq_3.__task_hours AS task_hours
  FROM (
    -- Read Elements From Semantic Model 'tasks_source'
    -- Metric Time Dimension 'ds'
    -- Constrain Time Range to [2020-01-01T00:00:00, 2020-01-02T00:00:00]
    SELECT
      DATE_TRUNC('day', ds) AS metric_time__day
      , employee_id AS employee
      , task_hours AS __task_hours
    FROM ***************************.fct_tasks tasks_source_src_36000
    WHERE DATE_TRUNC('day', ds) BETWEEN timestamp '2020-01-01' AND timestamp '2020-01-02'
  ) subq_3
  LEFT OUTER JOIN
    ***************************.dim_employees employees_source_src_36000
  ON
    subq_3.employee = employees_source_src_36000.employee_id
) subq_7
WHERE (employee__employee_key IN ('e2') OR employee__employee_key IN (WITH RECURSIVE descendant_of_tree(descendant_of_value) AS (SELECT (employee_id) FROM ***************************.dim_employees WHERE (manager_id) IN ('e2') UNION SELECT (employee_id) FROM ***************************.dim_employees JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value) SELECT descendant_of_value FROM descendant_of_tree))
GROUP BY
  metric_time__day
  , employee__employee_key
ORDER BY employee__employee_key
LIMIT 5
