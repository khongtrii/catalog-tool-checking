import polars as pl
import os

base = "D:/Code/catalog-tool-checking/data/C621"

print("=== Files in data/C621 ===")
for root, dirs, files in os.walk(base):
    for f in files:
        p = os.path.join(root, f)
        print(p, os.path.getsize(p))

print("\n=== Att Cat_C621_RP.xlsx ===")
p = os.path.join(base, "Att Cat_C621_RP.xlsx")
df = pl.read_excel(p, infer_schema_length=0, read_options={"header_row": 0})
print("Shape:", df.shape)
print("Columns:", df.columns)
print(df.head(3).to_dicts())
