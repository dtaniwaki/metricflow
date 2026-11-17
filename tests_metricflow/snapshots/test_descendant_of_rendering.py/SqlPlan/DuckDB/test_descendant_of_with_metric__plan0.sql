test_name: test_descendant_of_with_metric
test_filename: test_descendant_of_rendering.py
docstring:
  Check the SQL for a where filter that limits an employee to one employee and the ones reporting to them.
sql_engine: DuckDB
---
-- Write to DataTable
SELECT
  subq_9.employee__employee_key
  , subq_9.task_hours
FROM (
  -- Compute Metrics via Expressions
  SELECT
    subq_8.employee__employee_key
    , subq_8.__task_hours AS task_hours
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      subq_7.employee__employee_key
      , SUM(subq_7.__task_hours) AS __task_hours
    FROM (
      -- Select: ['__task_hours', 'employee__employee_key']
      SELECT
        subq_6.employee__employee_key
        , subq_6.__task_hours
      FROM (
        -- Constrain Output with WHERE
        SELECT
          subq_5.task_hours AS __task_hours
          , subq_5.employee__employee_key
        FROM (
          -- Select: ['__task_hours', 'employee__employee_key']
          SELECT
            subq_4.employee__employee_key
            , subq_4.__task_hours AS task_hours
          FROM (
            -- Join Standard Outputs
            SELECT
              subq_3.employee_key AS employee__employee_key
              , subq_1.ds__day AS ds__day
              , subq_1.ds__week AS ds__week
              , subq_1.ds__month AS ds__month
              , subq_1.ds__quarter AS ds__quarter
              , subq_1.ds__year AS ds__year
              , subq_1.ds__extract_year AS ds__extract_year
              , subq_1.ds__extract_quarter AS ds__extract_quarter
              , subq_1.ds__extract_month AS ds__extract_month
              , subq_1.ds__extract_day AS ds__extract_day
              , subq_1.ds__extract_dow AS ds__extract_dow
              , subq_1.ds__extract_doy AS ds__extract_doy
              , subq_1.task__ds__day AS task__ds__day
              , subq_1.task__ds__week AS task__ds__week
              , subq_1.task__ds__month AS task__ds__month
              , subq_1.task__ds__quarter AS task__ds__quarter
              , subq_1.task__ds__year AS task__ds__year
              , subq_1.task__ds__extract_year AS task__ds__extract_year
              , subq_1.task__ds__extract_quarter AS task__ds__extract_quarter
              , subq_1.task__ds__extract_month AS task__ds__extract_month
              , subq_1.task__ds__extract_day AS task__ds__extract_day
              , subq_1.task__ds__extract_dow AS task__ds__extract_dow
              , subq_1.task__ds__extract_doy AS task__ds__extract_doy
              , subq_1.metric_time__day AS metric_time__day
              , subq_1.metric_time__week AS metric_time__week
              , subq_1.metric_time__month AS metric_time__month
              , subq_1.metric_time__quarter AS metric_time__quarter
              , subq_1.metric_time__year AS metric_time__year
              , subq_1.metric_time__extract_year AS metric_time__extract_year
              , subq_1.metric_time__extract_quarter AS metric_time__extract_quarter
              , subq_1.metric_time__extract_month AS metric_time__extract_month
              , subq_1.metric_time__extract_day AS metric_time__extract_day
              , subq_1.metric_time__extract_dow AS metric_time__extract_dow
              , subq_1.metric_time__extract_doy AS metric_time__extract_doy
              , subq_1.employee AS employee
              , subq_1.task__employee AS task__employee
              , subq_1.task_kind AS task_kind
              , subq_1.task__task_kind AS task__task_kind
              , subq_1.__task_hours AS __task_hours
              , subq_1.__filtered_task_hours AS __filtered_task_hours
            FROM (
              -- Metric Time Dimension 'ds'
              SELECT
                subq_0.ds__day
                , subq_0.ds__week
                , subq_0.ds__month
                , subq_0.ds__quarter
                , subq_0.ds__year
                , subq_0.ds__extract_year
                , subq_0.ds__extract_quarter
                , subq_0.ds__extract_month
                , subq_0.ds__extract_day
                , subq_0.ds__extract_dow
                , subq_0.ds__extract_doy
                , subq_0.task__ds__day
                , subq_0.task__ds__week
                , subq_0.task__ds__month
                , subq_0.task__ds__quarter
                , subq_0.task__ds__year
                , subq_0.task__ds__extract_year
                , subq_0.task__ds__extract_quarter
                , subq_0.task__ds__extract_month
                , subq_0.task__ds__extract_day
                , subq_0.task__ds__extract_dow
                , subq_0.task__ds__extract_doy
                , subq_0.ds__day AS metric_time__day
                , subq_0.ds__week AS metric_time__week
                , subq_0.ds__month AS metric_time__month
                , subq_0.ds__quarter AS metric_time__quarter
                , subq_0.ds__year AS metric_time__year
                , subq_0.ds__extract_year AS metric_time__extract_year
                , subq_0.ds__extract_quarter AS metric_time__extract_quarter
                , subq_0.ds__extract_month AS metric_time__extract_month
                , subq_0.ds__extract_day AS metric_time__extract_day
                , subq_0.ds__extract_dow AS metric_time__extract_dow
                , subq_0.ds__extract_doy AS metric_time__extract_doy
                , subq_0.employee
                , subq_0.task__employee
                , subq_0.task_kind
                , subq_0.task__task_kind
                , subq_0.__task_hours
                , subq_0.__filtered_task_hours
              FROM (
                -- Read Elements From Semantic Model 'tasks_source'
                SELECT
                  tasks_source_src_36000.task_hours AS __task_hours
                  , tasks_source_src_36000.task_hours AS __filtered_task_hours
                  , DATE_TRUNC('day', tasks_source_src_36000.ds) AS ds__day
                  , DATE_TRUNC('week', tasks_source_src_36000.ds) AS ds__week
                  , DATE_TRUNC('month', tasks_source_src_36000.ds) AS ds__month
                  , DATE_TRUNC('quarter', tasks_source_src_36000.ds) AS ds__quarter
                  , DATE_TRUNC('year', tasks_source_src_36000.ds) AS ds__year
                  , EXTRACT(year FROM tasks_source_src_36000.ds) AS ds__extract_year
                  , EXTRACT(quarter FROM tasks_source_src_36000.ds) AS ds__extract_quarter
                  , EXTRACT(month FROM tasks_source_src_36000.ds) AS ds__extract_month
                  , EXTRACT(day FROM tasks_source_src_36000.ds) AS ds__extract_day
                  , EXTRACT(isodow FROM tasks_source_src_36000.ds) AS ds__extract_dow
                  , EXTRACT(doy FROM tasks_source_src_36000.ds) AS ds__extract_doy
                  , tasks_source_src_36000.task_kind
                  , DATE_TRUNC('day', tasks_source_src_36000.ds) AS task__ds__day
                  , DATE_TRUNC('week', tasks_source_src_36000.ds) AS task__ds__week
                  , DATE_TRUNC('month', tasks_source_src_36000.ds) AS task__ds__month
                  , DATE_TRUNC('quarter', tasks_source_src_36000.ds) AS task__ds__quarter
                  , DATE_TRUNC('year', tasks_source_src_36000.ds) AS task__ds__year
                  , EXTRACT(year FROM tasks_source_src_36000.ds) AS task__ds__extract_year
                  , EXTRACT(quarter FROM tasks_source_src_36000.ds) AS task__ds__extract_quarter
                  , EXTRACT(month FROM tasks_source_src_36000.ds) AS task__ds__extract_month
                  , EXTRACT(day FROM tasks_source_src_36000.ds) AS task__ds__extract_day
                  , EXTRACT(isodow FROM tasks_source_src_36000.ds) AS task__ds__extract_dow
                  , EXTRACT(doy FROM tasks_source_src_36000.ds) AS task__ds__extract_doy
                  , tasks_source_src_36000.task_kind AS task__task_kind
                  , tasks_source_src_36000.employee_id AS employee
                  , tasks_source_src_36000.employee_id AS task__employee
                FROM ***************************.fct_tasks tasks_source_src_36000
              ) subq_0
            ) subq_1
            LEFT OUTER JOIN (
              -- Select: ['employee_key', 'employee']
              SELECT
                subq_2.employee
                , subq_2.employee_key
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
              ) subq_2
            ) subq_3
            ON
              subq_1.employee = subq_3.employee
          ) subq_4
        ) subq_5
        WHERE (employee__employee_key IN ('e2') OR employee__employee_key IN (WITH RECURSIVE descendant_of_tree(descendant_of_value) AS (SELECT (employee_id) FROM ***************************.dim_employees WHERE (manager_id) IN ('e2') UNION SELECT (employee_id) FROM ***************************.dim_employees JOIN descendant_of_tree ON (manager_id) = descendant_of_tree.descendant_of_value) SELECT descendant_of_value FROM descendant_of_tree))
      ) subq_6
    ) subq_7
    GROUP BY
      subq_7.employee__employee_key
  ) subq_8
) subq_9
