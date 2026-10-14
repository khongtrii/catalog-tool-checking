import polars as pl
import unicodedata
import re
from datetime import date, datetime
# Required Column of Catalog
REQUIRED_CATALOG_COLUMNS = [
    'GROUPED DIVISION', 'DIVISION', 'DEPARTMENT', 'GOLD CODE', 'TILLCODE', 'SV',
    'PRODUCT NAME VIE', 'UNIT', 'START DATE', 'END DATE', 'SYSTEM GOLD VLL', 'REGION NORTH SOUTH CENTER ALL',
    'PAGE', 'PAGE DIGITAL', 'THEMATIC', 'POSITION', 'NORMAL SELLING PRICE VND', 'PROMOTIONAL SELLING PRICE VND',
    'MULTIBUYCOMBO SELLING PRICE VND', 'DISCOUNT TO CUSTOMER VND', '% DISCOUNT TO CUSTOMER', 'PROMO TYPE',
    'PROMO DETAILS', 'PROMOTION GIFT', 'GIFT VALUE', 'NOTE', 'THE1 POINTS', 'THE1 EXCLUSIVE PRICE VND', 'NOTE_1']

# Required Header Columns
HEADER_COLUMNS = [
    'GROUPED DIVISION', 'DIVISION', 'DEPARTMENT', 'GOLD CODE', 'TILLCODE', 'SV'
]

# Required Data Columns
REQUIRED_DATA_COLUMNS = [
    'GOLD CODE', 'SV', 'NORMAL SELLING PRICE VND', 'PROMOTIONAL SELLING PRICE VND'
]
# Normalize Function
def normalize(value):
    if value is None:
        return None

    value = unicodedata.normalize("NFKC", str(value))
    value = re.sub(r"[/\r\n\t\f\v]+", " ", value)
    value = re.sub(r"[^\w\s%]", "", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip().upper()

# Mapping Column
def map_columns(df, required_columns):
    mapping = {}
    used = set()

    for required in required_columns:
        if required in df.columns:
            used.add(required)
            continue

        matches = [
            col for col in df.columns
            if col.startswith(required + " ") and col not in used
        ]

        if len(matches) == 1:
            mapping[matches[0]] = required
            used.add(matches[0])

    df = df.rename(mapping)

    return df.select([
        pl.col(col) if col in df.columns
        else pl.lit(None, dtype=pl.String).alias(col)
        for col in required_columns
    ])

# Scan Header
def scan_header(pth, sheet_name):
    data = pl.read_excel(
        pth,
        infer_schema_length=0,
        sheet_name=sheet_name
    )

    has_header = False

    for i in range(0, 10, 1):
        if all(col in data.row(i) for col in HEADER_COLUMNS):
            has_header = True
            break

    if has_header:
        return i + 1
    else:
        raise ValueError(f"Could not find header of sheet {sheet_name} !!!")


def parse_target_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    for date_format in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    raise ValueError("target_date must use DD/MM/YYYY or DD/MM/YY format")


def select_effective_price(query, target_date):
    target_date = parse_target_date(target_date)

    query = query.with_columns(
        pl.col("START_DATE")
        .str.strptime(pl.Date, format="%d/%m/%y", strict=False)
        .alias("_NORMAL_START_DATE"),
        pl.col("END_DATE")
        .str.strptime(pl.Date, format="%d/%m/%y", strict=False)
        .alias("_NORMAL_END_DATE"),
        pl.col("START_DATE_KM")
        .str.strptime(pl.Date, format="%d/%m/%y", strict=False)
        .alias("_PROMO_START_DATE"),
        pl.col("END_DATE_KM")
        .str.strptime(pl.Date, format="%d/%m/%y", strict=False)
        .alias("_PROMO_END_DATE"),
    )

    normal_is_valid = (
        pl.col("GIA_NORMAL").is_not_null()
        & (pl.col("_NORMAL_START_DATE") <= pl.lit(target_date))
        & (pl.col("_NORMAL_END_DATE") >= pl.lit(target_date))
    )
    promo_is_valid = (
        pl.col("GIA_KM").is_not_null()
        & (pl.col("_PROMO_START_DATE") <= pl.lit(target_date))
        & (pl.col("_PROMO_END_DATE") >= pl.lit(target_date))
    )

    return (
        query.with_columns(
            pl.when(promo_is_valid)
            .then(pl.col("GIA_KM"))
            .when(normal_is_valid)
            .then(pl.col("GIA_NORMAL"))
            .alias("FINAL PRICE"),
            pl.when(promo_is_valid)
            .then(pl.col("_PROMO_START_DATE"))
            .when(normal_is_valid)
            .then(pl.col("_NORMAL_START_DATE"))
            .alias("VALID START DATE"),
            pl.when(promo_is_valid)
            .then(pl.col("_PROMO_END_DATE"))
            .when(normal_is_valid)
            .then(pl.col("_NORMAL_END_DATE"))
            .alias("VALID END DATE"),
            pl.when(promo_is_valid)
            .then(pl.lit("KM"))
            .when(normal_is_valid)
            .then(pl.lit("NORMAL"))
            .alias("PRICE TYPE"),
        )
        .drop(
            "_NORMAL_START_DATE",
            "_NORMAL_END_DATE",
            "_PROMO_START_DATE",
            "_PROMO_END_DATE",
        )
    )


file_path = "/content/C621.xlsx"
sheet_name = "MB+VINH"
target_date = "08/10/2026"
df = pl.read_excel(
    file_path,
    infer_schema_length=0,
    read_options={"header_row": scan_header(file_path, sheet_name)},
    sheet_name=sheet_name
)
df = df.rename({col: normalize(col) for col in df.columns})
df = map_columns(df, REQUIRED_CATALOG_COLUMNS)
df = df.drop_nulls(subset=REQUIRED_DATA_COLUMNS)
df = df.with_columns(
    pl.lit(sheet_name).alias("REGION")
)
df = df.with_columns(
    pl.coalesce(
        pl.col("PROMOTIONAL SELLING PRICE VND"),
        pl.col("NORMAL SELLING PRICE VND")
    )
    .fill_null("None Price")
    .alias("FINAL PRICE")
)
df = df.with_columns(
    pl.lit("112").alias("SUGGEST SITE")
)
df = df.with_columns(
    pl.concat_str(
        ["GOLD CODE", "SV", "SUGGEST SITE"],
        separator="-"
    ).alias("KEY")
)
df = df.filter(
    pl.col('FINAL PRICE') != 'None Price'
)
df = df.with_columns(pl.col('FINAL PRICE').cast(pl.Int64))
query = pl.read_excel('/content/query_price.xlsx', infer_schema_length=0)
query = query.with_columns(
    pl.concat_str(
        ["GOLD_CODE", "SV", "CH"],
        separator="-"
    ).alias("KEY")
)
query = select_effective_price(query, target_date)
query = query.filter(
    (pl.col("DIVISION") != "DIVISION") &
    (pl.col("FINAL PRICE").is_not_null()) &
    (pl.col("VALID START DATE").is_not_null()) &
    (pl.col("VALID END DATE").is_not_null())
)
query = query.with_columns(pl.col('FINAL PRICE').cast(pl.Int64))
query = query.with_columns(
    pl.col(["VALID START DATE", "VALID END DATE"])
    .dt.strftime("%d/%m/%Y")
)
query
