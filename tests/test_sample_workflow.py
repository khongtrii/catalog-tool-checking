from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
import unittest
from zipfile import ZipFile

from catalog_checker import (
    build_result_zip,
    compare_with_query,
    read_catalog_sheet,
    read_effective_query,
    workbook_sheet_info,
)


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
QUERY_PATH = DATA_ROOT / "C621" / "D-1" / "query_price.xlsx"


@unittest.skipUnless(QUERY_PATH.is_file(), "Local sample data is not available")
class SampleWorkflowTests(unittest.TestCase):
    def test_query_catalog_and_zip_pipeline(self) -> None:
        query = read_effective_query(QUERY_PATH.read_bytes(), date(2026, 10, 8))
        self.assertGreater(query.height, 0)
        site = str(query["KEY"][0]).rsplit("-", 1)[-1]

        selected_file = None
        selected_sheet = None
        for path in sorted(DATA_ROOT.rglob("*.xlsx")):
            if path == QUERY_PATH or path.name.startswith("CataPriceCheck"):
                continue
            try:
                processable = [
                    item for item in workbook_sheet_info(path.read_bytes()) if item["processable"]
                ]
            except Exception:
                continue
            if processable:
                selected_file = path
                selected_sheet = processable[0]
                break

        self.assertIsNotNone(selected_file, "No processable sample catalogue was found")
        catalog = read_catalog_sheet(
            selected_file.read_bytes(),
            selected_sheet["name"],
            site,
            selected_sheet["header_row"],
        )
        compared = compare_with_query(catalog, query)
        archive_bytes, _ = build_result_zip(
            [(selected_file.stem, compared)],
            [],
            date(2026, 10, 8),
        )
        with ZipFile(BytesIO(archive_bytes)) as archive:
            self.assertIsNone(archive.testzip())


if __name__ == "__main__":
    unittest.main()
