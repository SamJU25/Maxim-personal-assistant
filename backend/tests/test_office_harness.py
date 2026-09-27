"""
Unit tests for Office & Spreadsheet Harness (office_harness.py).
Verifies:
1. Coordinate math (letters <-> indices, cell names, ranges).
2. Formula evaluation (SUM, AVERAGE, COUNT, MIN, MAX, IF, CONCAT, arithmetic).
3. Workbook and sheet creation, reading grid matrix.
4. Cell updates, computed values, and Git-style revisions.
5. Revision rollback mechanism.
6. CSV import and CSV export.
7. Markdown table generation and vault sync.
8. FastAPI endpoints.
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from office_harness import (
    OfficeHarnessEngine,
    col_str_to_index,
    col_index_to_str,
    cell_name_to_coords,
    coords_to_cell_name,
    parse_range_notation,
    FormulaEvaluator,
)
from server import app

client = TestClient(app)

def test_coordinate_and_range_math():
    """Verify coordinate conversions and range parsing."""
    assert col_str_to_index("A") == 0
    assert col_str_to_index("Z") == 25
    assert col_str_to_index("AA") == 26
    assert col_str_to_index("AB") == 27

    assert col_index_to_str(0) == "A"
    assert col_index_to_str(25) == "Z"
    assert col_index_to_str(26) == "AA"

    assert cell_name_to_coords("A1") == (0, 0)
    assert cell_name_to_coords("B5") == (4, 1)
    assert cell_name_to_coords("C10") == (9, 2)
    assert coords_to_cell_name(0, 0) == "A1"
    assert coords_to_cell_name(4, 1) == "B5"

    range_coords = parse_range_notation("A1:B2")
    assert range_coords == [(0, 0), (0, 1), (1, 0), (1, 1)]

def test_formula_evaluator_functions():
    """Verify standard formula calculations."""
    grid = {
        (0, 0): 10,   # A1
        (1, 0): 20,   # A2
        (2, 0): 30,   # A3
        (0, 1): "Yes", # B1
    }
    evaluator = FormulaEvaluator(lambda r, c: grid.get((r, c)))

    # SUM
    assert evaluator.evaluate("=SUM(A1:A3)") == 60
    # AVERAGE
    assert evaluator.evaluate("=AVERAGE(A1:A3)") == 20
    # COUNT
    assert evaluator.evaluate("=COUNT(A1:A3)") == 3
    # MIN & MAX
    assert evaluator.evaluate("=MIN(A1:A3)") == 10
    assert evaluator.evaluate("=MAX(A1:A3)") == 30
    # IF
    assert evaluator.evaluate('=IF(A1>5, "Pass", "Fail")') == "Pass"
    assert evaluator.evaluate('=IF(A1>50, "Pass", "Fail")') == "Fail"
    # CONCAT
    assert evaluator.evaluate('=CONCAT("Val: ", A1)') == "Val: 10"
    # Basic math
    assert evaluator.evaluate("=A1+A2") == 30
    assert evaluator.evaluate("=A1*2") == 20

def test_workbook_and_sheet_lifecycle(tmp_path: Path):
    """Verify workbook creation, cell updates, formula calculation, and grid retrieval."""
    engine = OfficeHarnessEngine(db_path=tmp_path / "office_test.db")
    wb = engine.create_workbook(title="Q3 Financials", description="Revenue and expenses", initial_sheet_names=["Summary", "Data"])

    assert wb.title == "Q3 Financials"
    assert len(wb.sheets) == 2
    sheet1_id = wb.sheets[0].id

    # Update cells with numbers and a formula
    updates = {
        "A1": "Category",
        "B1": "Amount",
        "A2": "Subscriptions",
        "B2": 1500,
        "A3": "Services",
        "B3": 2500,
        "A4": "Total",
        "B4": "=SUM(B2:B3)",
    }
    res = engine.update_cells(sheet_id=sheet1_id, cell_updates=updates, author="test_runner")
    assert res["status"] == "applied"
    assert res["modified_cells"] == 8

    # Read back grid
    grid = engine.read_sheet_grid(sheet_id=sheet1_id)
    assert grid["total_cells"] == 8
    cells = grid["cells"]
    assert cells["B4"]["computed_value"] == "4000"
    assert cells["B4"]["formula"] == "=SUM(B2:B3)"

def test_git_style_revisions_and_rollback(tmp_path: Path):
    """Verify cell diffs and full rollback to previous values."""
    engine = OfficeHarnessEngine(db_path=tmp_path / "rollback_test.db")
    wb = engine.create_workbook(title="Budget")
    sheet_id = wb.sheets[0].id

    # Commit 1
    engine.update_cells(sheet_id=sheet_id, cell_updates={"A1": "Original", "B1": 100})
    grid1 = engine.read_sheet_grid(sheet_id)
    assert grid1["cells"]["A1"]["computed_value"] == "Original"

    # Commit 2
    commit2 = engine.update_cells(sheet_id=sheet_id, cell_updates={"A1": "Modified", "B1": 500})
    rev2_id = commit2["revision_id"]
    grid2 = engine.read_sheet_grid(sheet_id)
    assert grid2["cells"]["A1"]["computed_value"] == "Modified"
    assert grid2["cells"]["B1"]["computed_value"] == "500"

    # Rollback Commit 2
    rb_res = engine.rollback_revision(sheet_id=sheet_id, revision_id=rev2_id)
    assert rb_res["status"] == "applied"
    grid3 = engine.read_sheet_grid(sheet_id)
    assert grid3["cells"]["A1"]["computed_value"] == "Original"
    assert grid3["cells"]["B1"]["computed_value"] == "100"

def test_csv_import_and_export(tmp_path: Path):
    """Verify importing and exporting CSV datasets."""
    engine = OfficeHarnessEngine(db_path=tmp_path / "csv_test.db")
    wb = engine.create_workbook(title="CSV Test")
    sheet_id = wb.sheets[0].id

    csv_data = "Item,Qty,Price\nLaptop,2,1200\nMouse,5,25"
    engine.import_csv(sheet_id=sheet_id, csv_text_or_path=csv_data)

    grid = engine.read_sheet_grid(sheet_id)
    assert grid["cells"]["A1"]["computed_value"] == "Item"
    assert grid["cells"]["B2"]["computed_value"] == "2"
    assert grid["cells"]["C3"]["computed_value"] == "25"

    exported = engine.export_csv(sheet_id=sheet_id)
    assert "Item,Qty,Price" in exported
    assert "Laptop,2,1200" in exported

def test_markdown_table_generation(tmp_path: Path):
    """Verify generating Markdown tables and optional vault synchronization."""
    engine = OfficeHarnessEngine(db_path=tmp_path / "md_test.db")
    wb = engine.create_workbook(title="Markdown Test")
    sheet_id = wb.sheets[0].id

    engine.update_cells(sheet_id=sheet_id, cell_updates={
        "A1": "Project", "B1": "Status",
        "A2": "MaxIM V2", "B2": "Active",
        "A3": "Hermes", "B3": "Integrated",
    })

    md = engine.export_markdown_table(sheet_id=sheet_id)
    assert "| Project | Status |" in md
    assert "| --- | --- |" in md
    assert "| MaxIM V2 | Active |" in md
    assert "| Hermes | Integrated |" in md

def test_fastapi_office_endpoints():
    """Verify /api/office endpoints create workbooks, update cells, and read grids."""
    # 1. Create workbook
    res_create = client.post("/api/office/workbook", json={
        "title": "API Test Workbook",
        "description": "Created via test",
        "sheet_names": ["Main"],
    })
    assert res_create.status_code == 200
    data = res_create.json()
    sheet_id = data["workbook"]["sheets"][0]["id"]

    # 2. Update cells
    res_update = client.post(f"/api/office/sheet/{sheet_id}/cells", json={
        "updates": {"A1": "TestLabel", "B1": 999},
        "author": "api_test",
    })
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "applied"

    # 3. Read grid
    res_read = client.get(f"/api/office/sheet/{sheet_id}")
    assert res_read.status_code == 200
    assert res_read.json()["cells"]["A1"]["computed_value"] == "TestLabel"

    # 4. Export markdown
    res_md = client.post(f"/api/office/sheet/{sheet_id}/export-markdown", json={})
    assert res_md.status_code == 200
    assert "TestLabel" in res_md.json()["markdown_table"]
