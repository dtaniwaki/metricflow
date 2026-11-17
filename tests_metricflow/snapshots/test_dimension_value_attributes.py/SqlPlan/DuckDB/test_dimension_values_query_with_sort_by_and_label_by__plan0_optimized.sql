test_name: test_dimension_values_query_with_sort_by_and_label_by
test_filename: test_dimension_value_attributes.py
docstring:
  The query for the values of a dimension that declares `sort_by` and `label_by` selects the label and sort.
sql_engine: DuckDB
---
-- Read Elements From Semantic Model 'product_source'
-- Select: ['product__category_code', 'product__category_name', 'product__category_rank']
-- Select: ['product__category_code', 'product__category_name', 'product__category_rank']
-- Order By ['product__category_rank', 'product__category_code']
-- Write to DataTable
SELECT
  category_code AS product__category_code
  , category_rank AS product__category_rank
  , category_name AS product__category_name
FROM ***************************.product_table product_source_src_36000
GROUP BY
  category_code
  , category_rank
  , category_name
ORDER BY product__category_rank, product__category_code
