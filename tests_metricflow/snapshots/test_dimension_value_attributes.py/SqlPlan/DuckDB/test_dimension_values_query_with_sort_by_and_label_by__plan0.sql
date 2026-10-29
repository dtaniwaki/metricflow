test_name: test_dimension_values_query_with_sort_by_and_label_by
test_filename: test_dimension_value_attributes.py
docstring:
  The query for the values of a dimension that declares `sort_by` and `label_by` selects the label and sort.
sql_engine: DuckDB
---
-- Write to DataTable
SELECT
  subq_3.product__category_code
  , subq_3.product__category_rank
  , subq_3.product__category_name
FROM (
  -- Order By ['product__category_rank', 'product__category_code']
  SELECT
    subq_2.product__category_code
    , subq_2.product__category_rank
    , subq_2.product__category_name
  FROM (
    -- Select: ['product__category_code', 'product__category_name', 'product__category_rank']
    SELECT
      subq_1.product__category_code
      , subq_1.product__category_rank
      , subq_1.product__category_name
    FROM (
      -- Select: ['product__category_code', 'product__category_name', 'product__category_rank']
      SELECT
        subq_0.product__category_code
        , subq_0.product__category_rank
        , subq_0.product__category_name
      FROM (
        -- Read Elements From Semantic Model 'product_source'
        SELECT
          product_source_src_36000.category_code
          , product_source_src_36000.category_rank
          , product_source_src_36000.category_name
          , product_source_src_36000.brand_code
          , product_source_src_36000.brand_name
          , product_source_src_36000.region_code
          , product_source_src_36000.region_label
          , product_source_src_36000.color
          , product_source_src_36000.category_code AS product__category_code
          , product_source_src_36000.category_rank AS product__category_rank
          , product_source_src_36000.category_name AS product__category_name
          , product_source_src_36000.brand_code AS product__brand_code
          , product_source_src_36000.brand_name AS product__brand_name
          , product_source_src_36000.region_code AS product__region_code
          , product_source_src_36000.region_label AS product__region_label
          , product_source_src_36000.color AS product__color
          , product_source_src_36000.product_id AS product
        FROM ***************************.product_table product_source_src_36000
      ) subq_0
    ) subq_1
    GROUP BY
      subq_1.product__category_code
      , subq_1.product__category_rank
      , subq_1.product__category_name
  ) subq_2
  ORDER BY subq_2.product__category_rank, subq_2.product__category_code
) subq_3
