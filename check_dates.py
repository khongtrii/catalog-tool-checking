import polars as pl
import os
from collections import Counter

base_d1 = "D:/Code/catalog-tool-checking/data/C621/D-1"
q = pl.read_excel(os.path.join(base_d1, "query_price.xlsx"), infer_schema_length=0)

for c in ["START_DATE","END_DATE","START_DATE_KM","END_DATE_KM"]:
    col = q[c]
    print(f"=== {c} ===")
    print("nulls:", col.is_null().sum())
    # distinct non-null values, top 15
    print("top non-null values:", col.drop_nulls().value_counts().head(15).to_dicts())
    # check format: len and '/'
    lens = col.drop_nulls().str.len().unique().sort()
    print("string lens:", lens[:10])
