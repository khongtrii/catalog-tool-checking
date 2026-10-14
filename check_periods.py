import polars as pl
import os

base_d3 = "D:/Code/catalog-tool-checking/data/C621/D-3"
base_d1 = "D:/Code/catalog-tool-checking/data/C621/D-1"

d3 = pl.read_excel(os.path.join(base_d3, "Selling price _Cata list 051026.xlsx"), infer_schema_length=0)
q = pl.read_excel(os.path.join(base_d1, "query_price.xlsx"), infer_schema_length=0)

print("D3 shape:", d3.shape, "cols:", d3.columns)
print("Q shape:", q.shape, "cols:", q.columns)

# Join query with d3 on GOLD_CODE+SV+CH
key = ["GOLD_CODE", "SV", "CH"]
joined = q.join(d3, on=key, how="left", suffix="_d3")

cols_period = ["START_DATE", "END_DATE", "START_DATE_KM", "END_DATE_KM"]
print("\n=== Compare query vs D3 periods for matched rows ===")
for c in cols_period:
    qcol = c
    d3col = c + "_d3"
    # check if they differ for any matched row
    diff = joined.filter(pl.col(qcol).is_not_null() & pl.col(d3col).is_not_null() & (pl.col(qcol) != pl.col(d3col)))
    print(f"{c}: matched rows with diff = {diff.height}")

# count unmatched query rows (no d3 match)
print("\nQuery rows with no D3 match:", joined.filter(pl.col("GIA_KM_d3").is_null()).height)

# show a few example rows with differing periods
print("\nExample rows where START_DATE differs:")
print(joined.filter(pl.col("START_DATE") != pl.col("START_DATE_d3")).select(["DIVISION","GOLD_CODE","SV","CH","START_DATE","START_DATE_d3","END_DATE","END_DATE_d3"]).head(5).to_dicts())
