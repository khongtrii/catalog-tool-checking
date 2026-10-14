from __future__ import annotations

from datetime import date

import polars as pl
import streamlit as st

from catalog_checker import (
    build_result_zip,
    compare_with_query,
    derive_output_sheet_name,
    read_catalog_sheet,
    read_effective_query,
    workbook_sheet_info,
)


OPTIONAL_FILE_SLOTS = [
    ("5102_QA_10", False),
    ("5102_QA_11", False),
    ("6922_Vynamic", True),
    ("Price Cata", False),
    ("Price Comple", False),
]


st.set_page_config(page_title="Catalog Price Checker", page_icon="📋", layout="wide")
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 17px;
    }
    h1 {
        font-size: 2.35rem !important;
    }
    h2, h3 {
        font-size: 1.55rem !important;
    }
    label, [data-testid="stWidgetLabel"] p,
    [data-testid="stFileUploader"] p,
    [data-testid="stCaptionContainer"] p {
        font-size: 1.05rem !important;
    }
    .stButton button, .stDownloadButton button {
        font-size: 1.05rem !important;
        min-height: 2.75rem;
    }
    [data-testid="stDataFrame"] {
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Catalog Price Checker")
st.caption("Đối chiếu giá catalogue với giá hiệu lực tại cửa hàng theo ngày chỉ định.")


@st.cache_data(show_spinner=False)
def inspect_workbook(file_bytes: bytes):
    return workbook_sheet_info(file_bytes)


query_file = st.file_uploader("1. Chọn file query giá", type=["xlsx"])
target_date = st.date_input("2. Ngày kiểm tra", value=date.today(), format="DD/MM/YYYY")
catalog_files = st.file_uploader(
    "3. Chọn các file catalogue",
    type=["xlsx"],
    accept_multiple_files=True,
)

selections: list[dict[str, object]] = []
if catalog_files:
    st.subheader("4. Chọn sheet cần xử lý")
    for file_index, uploaded_file in enumerate(catalog_files):
        file_bytes = uploaded_file.getvalue()
        try:
            sheet_info = inspect_workbook(file_bytes)
        except Exception as error:
            st.error(f"Không đọc được {uploaded_file.name}: {error}")
            continue

        header_rows = {item["name"]: item["header_row"] for item in sheet_info}
        with st.expander(uploaded_file.name, expanded=True):
            selected_sheets = st.multiselect(
                "Sheets/REGION",
                options=[item["name"] for item in sheet_info],
                default=[],
                key=f"sheets_{file_index}_{uploaded_file.name}",
                placeholder="Chọn một hoặc nhiều sheet cần xử lý",
                help=(
                    "App không tự động chọn sheet. Chỉ những sheet bạn chọn và có "
                    "header catalogue hợp lệ mới được xử lý."
                ),
            )
            invalid = [name for name in selected_sheets if header_rows[name] is None]
            if invalid:
                st.warning("Không tìm thấy header catalogue: " + ", ".join(invalid))
            output_sheet = st.text_input(
                "Tên sheet output",
                value=derive_output_sheet_name(uploaded_file.name),
                key=f"output_{file_index}_{uploaded_file.name}",
            )

        for region in selected_sheets:
            if header_rows[region] is not None:
                selections.append(
                    {
                        "file_index": file_index,
                        "file_name": uploaded_file.name,
                        "file_bytes": file_bytes,
                        "output_sheet": output_sheet,
                        "region": region,
                        "header_row": header_rows[region],
                    }
                )

site_values: dict[tuple[int, str], str] = {}
if selections:
    st.subheader("5. Khai báo SUGGEST SITE")
    site_table = pl.DataFrame(
        {
            "FILE": [item["file_name"] for item in selections],
            "REGION": [item["region"] for item in selections],
            "SUGGEST SITE": ["" for _ in selections],
        }
    ).to_pandas()
    edited_sites = st.data_editor(
        site_table,
        hide_index=True,
        width="stretch",
        disabled=["FILE", "REGION"],
        column_config={
            "SUGGEST SITE": st.column_config.TextColumn(
                "SUGGEST SITE",
                required=True,
                help="Mã CH dùng để tạo KEY GOLD CODE-SV-CH.",
            )
        },
        key="site_mapping",
    )
    for selection, (_, row) in zip(selections, edited_sites.iterrows()):
        site_values[(selection["file_index"], selection["region"])] = str(
            row["SUGGEST SITE"]
        ).strip()

st.subheader("6. Chọn file bổ sung")
selected_add_files: list[tuple[str, bytes, bool]] = []
for slot_name, use_dept in OPTIONAL_FILE_SLOTS:
    label_column, upload_column = st.columns([1, 3], vertical_alignment="center")
    with label_column:
        st.write(slot_name)
    with upload_column:
        uploaded_add_file = st.file_uploader(
            f"Chọn file {slot_name}",
            type=["xlsx"],
            key=f"additional_{slot_name}",
            label_visibility="collapsed",
        )
    if uploaded_add_file is not None:
        selected_add_files.append(
            (uploaded_add_file.name, uploaded_add_file.getvalue(), use_dept)
        )
st.caption(
    "Không bắt buộc chọn. 6922_Vynamic dùng DEPT; các file còn lại dùng DIVISION."
)

can_process = query_file is not None and bool(selections)
if st.button("Xử lý và tạo file kết quả", type="primary", disabled=not can_process):
    missing_sites = [
        f"{item['file_name']} / {item['region']}"
        for item in selections
        if not site_values[(item["file_index"], item["region"])]
    ]
    if missing_sites:
        st.error("Chưa nhập SUGGEST SITE cho: " + "; ".join(missing_sites))
    else:
        try:
            with st.spinner("Đang đọc query và đối chiếu giá..."):
                query = read_effective_query(query_file.getvalue(), target_date)
                grouped: dict[int, list[pl.DataFrame]] = {}
                metadata: dict[int, tuple[str, str]] = {}

                for item in selections:
                    file_index = item["file_index"]
                    catalog = read_catalog_sheet(
                        item["file_bytes"],
                        item["region"],
                        site_values[(file_index, item["region"])],
                        item["header_row"],
                    )
                    grouped.setdefault(file_index, []).append(catalog)
                    metadata[file_index] = (item["output_sheet"], item["file_name"])

                output_results = []
                summary_rows = []
                for file_index, frames in grouped.items():
                    combined = pl.concat(frames, how="vertical_relaxed")
                    compared = compare_with_query(combined, query)
                    output_sheet, file_name = metadata[file_index]
                    output_results.append((output_sheet, compared))
                    summary_rows.append(
                        {
                            "FILE": file_name,
                            "OUTPUT SHEET": output_sheet,
                            "CATALOG ROWS": combined.height,
                            "ROWS WITH QUERY PRICE": compared.height,
                            "ĐÚNG GIÁ": compared.filter(
                                pl.col("MDT NOTE") == "đúng giá"
                            ).height,
                            "LỆCH GIÁ": compared.filter(
                                pl.col("MDT NOTE") == "lệch giá"
                            ).height,
                        }
                    )

                zip_bytes, package_summary = build_result_zip(
                    output_results,
                    selected_add_files,
                    target_date,
                )

            st.success("Đã xử lý xong.")
            st.dataframe(summary_rows, width="stretch", hide_index=True)
            st.subheader("Nội dung file ZIP")
            st.dataframe(package_summary, width="stretch", hide_index=True)
            st.download_button(
                "Tải file ZIP kết quả",
                data=zip_bytes,
                file_name=f"catalog_price_check_{target_date:%Y%m%d}.zip",
                mime="application/zip",
                type="primary",
            )
        except Exception as error:
            st.exception(error)
