import polars as pl
import os

base = "D:/Code/catalog-tool-checking/data/C621/D-3"
p = os.path.join(base, "Selling price _Cata list 051026.xlsx")
print("path:", p, "exists:", os.path.exists(p))
df = pl.read_excel(p, infer_schema_length=0)
print("Shape:", df.shape)
print("Columns:", df.columns)
print("--- head 10 ---")
for r in df.head(10).to_dicts():
    print(r)
