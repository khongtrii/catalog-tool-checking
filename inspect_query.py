import polars as pl

qpath = "D:/Code/catalog-tool-checking/data/C621/D-1/query_price.xlsx"
print("path repr:", repr(qpath))
q = pl.read_excel(qpath, infer_schema_length=0)
print("=== query_price.xlsx ===")
print("Shape:", q.shape)
print("Columns:", q.columns)
print("--- head ---")
print(q.head(8).to_dicts())
print("--- dtypes ---")
for c in q.columns:
    print(c, q[c].dtype)
