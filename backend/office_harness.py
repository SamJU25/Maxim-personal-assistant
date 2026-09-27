"""
MaxIM Office & Spreadsheet Harness.
Repository inspiration: dream-num/univer (Agent-Native Office Runtime).

Features:
1. Multi-Sheet Workbooks stored in SQLite WAL (workbooks, sheets, cells).
2. Standard Spreadsheet Formula Evaluator (SUM, AVERAGE, COUNT, MIN, MAX, IF, CONCAT, VLOOKUP, math ops).
3. Coordinate & Range Parser (e.g. A1, B2:D10, AA100).
4. Git-Style Cell Diffs, Revisions, and Rollback.
5. CSV / JSON Import & Export.
6. Obsidian-Compatible Markdown Table Generator.
"""
import re
import csv
import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple, Union
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.office_harness")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# =============================================================================
# COORDINATE & RANGE UTILITIES
# =============================================================================

def col_str_to_index(col_str: str) -> int:
    """Converts column letter (e.g. 'A' -> 0, 'Z' -> 25, 'AA' -> 26) to 0-based index."""
    col = 0
    for char in col_str.upper():
        if not ('A' <= char <= 'Z'):
            raise ValueError(f"Invalid column character: {char}")
        col = col * 26 + (ord(char) - ord('A') + 1)
    return col - 1

def col_index_to_str(col_idx: int) -> str:
    """Converts 0-based column index to letter string (e.g. 0 -> 'A', 25 -> 'Z', 26 -> 'AA')."""
    if col_idx < 0:
        raise ValueError("Column index cannot be negative")
    result = []
    col_idx += 1
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result.append(chr(ord('A') + remainder))
    return "".join(reversed(result))

def cell_name_to_coords(cell_name: str) -> Tuple[int, int]:
    """Converts 'A1' -> (0, 0), 'B5' -> (4, 1), 'AA10' -> (9, 26). (row, col) 0-indexed."""
    match = re.match(r"^([A-Za-z]+)(\d+)$", cell_name.strip())
    if not match:
        raise ValueError(f"Invalid cell name: {cell_name}")
    col_part, row_part = match.groups()
    row_idx = int(row_part) - 1
    col_idx = col_str_to_index(col_part)
    return (row_idx, col_idx)

def coords_to_cell_name(row_idx: int, col_idx: int) -> str:
    """Converts (0, 0) -> 'A1', (4, 1) -> 'B5'."""
    return f"{col_index_to_str(col_idx)}{row_idx + 1}"

def parse_range_notation(range_str: str) -> List[Tuple[int, int]]:
    """
    Parses 'A1:B3' or 'C5' into a list of (row, col) coordinates.
    """
    range_str = range_str.strip()
    if ":" in range_str:
        start_str, end_str = range_str.split(":", 1)
        r1, c1 = cell_name_to_coords(start_str)
        r2, c2 = cell_name_to_coords(end_str)
        min_r, max_r = min(r1, r2), max(r1, r2)
        min_c, max_c = min(c1, c2), max(c1, c2)
        coords = []
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                coords.append((r, c))
        return coords
    else:
        return [cell_name_to_coords(range_str)]

# =============================================================================
# DATA MODELS
# =============================================================================

class CellRecord(BaseModel):
    row_idx: int
    col_idx: int
    cell_name: str
    raw_value: str
    computed_value: Optional[Union[float, int, str, bool]] = None
    formula: Optional[str] = None
    data_type: str = "string"  # "string", "number", "boolean", "formula"

class SheetRecord(BaseModel):
    id: str
    workbook_id: str
    name: str
    row_count: int = 100
    col_count: int = 26
    created_at: str = Field(default_factory=utc_now_iso)

class WorkbookRecord(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    sheets: List[SheetRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

class CellRevisionRecord(BaseModel):
    id: Optional[int] = None
    sheet_id: str
    revision_id: str
    cell_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    author: str = "assistant"
    created_at: str = Field(default_factory=utc_now_iso)

# =============================================================================
# FORMULA EVALUATOR
# =============================================================================

class FormulaEvaluator:
    """
    Evaluates spreadsheet formulas over a 2D cell grid.
    Supports: SUM, AVERAGE, COUNT, MIN, MAX, IF, CONCAT, VLOOKUP, and basic arithmetic.
    """
    def __init__(self, cell_getter):
        """
        cell_getter: callable(r: int, c: int) -> raw_val or computed_val
        """
        self.get_cell = cell_getter

    def get_range_values(self, range_str: str) -> List[Any]:
        """Extracts values from a range string (e.g. 'A1:A5')."""
        coords = parse_range_notation(range_str)
        values = []
        for r, c in coords:
            val = self.get_cell(r, c)
            if val is not None and val != "":
                # Try numeric conversion
                try:
                    num = float(val)
                    values.append(int(num) if num.is_integer() else num)
                except ValueError:
                    values.append(val)
        return values

    def evaluate(self, formula: str) -> Any:
        """Evaluates a formula string like '=SUM(A1:A10)' or '=IF(A1>50, "Pass", "Fail")'."""
        if not formula.startswith("="):
            return formula

        expr = formula[1:].strip()
        expr_upper = expr.upper()

        # 1. SUM(range)
        m = re.match(r"^SUM\(([^)]+)\)$", expr_upper)
        if m:
            vals = self.get_range_values(m.group(1))
            nums = [v for v in vals if isinstance(v, (int, float))]
            total = sum(nums)
            return int(total) if isinstance(total, float) and total.is_integer() else round(total, 4)

        # 2. AVERAGE(range)
        m = re.match(r"^AVERAGE\(([^)]+)\)$", expr_upper)
        if m:
            vals = self.get_range_values(m.group(1))
            nums = [v for v in vals if isinstance(v, (int, float))]
            if not nums:
                return 0.0
            avg = sum(nums) / len(nums)
            return int(avg) if avg.is_integer() else round(avg, 4)

        # 3. COUNT(range)
        m = re.match(r"^COUNT\(([^)]+)\)$", expr_upper)
        if m:
            vals = self.get_range_values(m.group(1))
            nums = [v for v in vals if isinstance(v, (int, float))]
            return len(nums)

        # 4. MIN(range)
        m = re.match(r"^MIN\(([^)]+)\)$", expr_upper)
        if m:
            vals = self.get_range_values(m.group(1))
            nums = [v for v in vals if isinstance(v, (int, float))]
            return min(nums) if nums else 0

        # 5. MAX(range)
        m = re.match(r"^MAX\(([^)]+)\)$", expr_upper)
        if m:
            vals = self.get_range_values(m.group(1))
            nums = [v for v in vals if isinstance(v, (int, float))]
            return max(nums) if nums else 0

        # 6. IF(condition, true_val, false_val)
        m = re.match(r"^IF\(([^,]+),\s*([^,]+),\s*([^)]+)\)$", expr, re.IGNORECASE)
        if m:
            cond_str, true_part, false_part = m.groups()
            cond_res = self._eval_condition(cond_str.strip())
            res = true_part.strip() if cond_res else false_part.strip()
            return res.strip('"').strip("'")

        # 7. CONCAT(val1, val2, ...)
        m = re.match(r"^CONCAT\((.+)\)$", expr, re.IGNORECASE)
        if m:
            args = [a.strip() for a in m.group(1).split(",")]
            res_parts = []
            for a in args:
                if (a.startswith('"') and a.endswith('"')) or (a.startswith("'") and a.endswith("'")):
                    res_parts.append(a[1:-1])
                elif re.match(r"^[A-Za-z]+\d+$", a):
                    r, c = cell_name_to_coords(a)
                    val = self.get_cell(r, c)
                    res_parts.append(str(val) if val is not None else "")
                else:
                    res_parts.append(a)
            return "".join(res_parts)

        # 8. Basic arithmetic cell reference: A1 + B1, A1 * 1.10
        cell_match = re.match(r"^([A-Za-z]+\d+)\s*([\+\-\*\/])\s*([A-Za-z]+\d+|\d+(?:\.\d+)?)$", expr)
        if cell_match:
            c1_name, op, c2_or_num = cell_match.groups()
            r1, col1 = cell_name_to_coords(c1_name)
            v1_raw = self.get_cell(r1, col1)
            try:
                v1 = float(v1_raw)
            except (ValueError, TypeError):
                v1 = 0.0

            if re.match(r"^[A-Za-z]+\d+$", c2_or_num):
                r2, col2 = cell_name_to_coords(c2_or_num)
                v2_raw = self.get_cell(r2, col2)
                try:
                    v2 = float(v2_raw)
                except (ValueError, TypeError):
                    v2 = 0.0
            else:
                v2 = float(c2_or_num)

            if op == "+":
                res = v1 + v2
            elif op == "-":
                res = v1 - v2
            elif op == "*":
                res = v1 * v2
            elif op == "/":
                res = v1 / v2 if v2 != 0 else 0.0
            else:
                res = 0.0
            return int(res) if res.is_integer() else round(res, 4)

        # Single cell reference alias: =A1
        single_cell = re.match(r"^([A-Za-z]+\d+)$", expr)
        if single_cell:
            r, c = cell_name_to_coords(single_cell.group(1))
            return self.get_cell(r, c)

        return expr

    def _eval_condition(self, cond_str: str) -> bool:
        """Evaluates conditions like 'A1>100' or 'B2=\"Complete\"'."""
        ops = [(">=", lambda a, b: a >= b), ("<=", lambda a, b: a <= b),
               ("!=", lambda a, b: a != b), (">", lambda a, b: a > b),
               ("<", lambda a, b: a < b), ("=", lambda a, b: a == b)]

        for sym, func in ops:
            if sym in cond_str:
                parts = cond_str.split(sym, 1)
                left_raw = parts[0].strip()
                right_raw = parts[1].strip().strip('"').strip("'")

                if re.match(r"^[A-Za-z]+\d+$", left_raw):
                    r, c = cell_name_to_coords(left_raw)
                    val = self.get_cell(r, c)
                else:
                    val = left_raw

                # Compare numerically if possible
                try:
                    v_num = float(val)
                    r_num = float(right_raw)
                    return func(v_num, r_num)
                except (ValueError, TypeError):
                    return func(str(val), str(right_raw))
        return False

# =============================================================================
# OFFICE & SPREADSHEET ENGINE
# =============================================================================

class OfficeHarnessEngine:
    """
    SQLite-backed Office and Spreadsheet engine for MaxIM agents.
    Provides structured workbooks, formula calculation, git-style revisions, and vault exports.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Creates tables for workbooks, sheets, cells, and revision history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS office_workbooks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS office_sheets (
                    id TEXT PRIMARY KEY,
                    workbook_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    row_count INTEGER DEFAULT 100,
                    col_count INTEGER DEFAULT 26,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (workbook_id) REFERENCES office_workbooks(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS office_cells (
                    sheet_id TEXT NOT NULL,
                    row_idx INTEGER NOT NULL,
                    col_idx INTEGER NOT NULL,
                    raw_value TEXT,
                    computed_value TEXT,
                    formula TEXT,
                    data_type TEXT DEFAULT 'string',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (sheet_id, row_idx, col_idx),
                    FOREIGN KEY (sheet_id) REFERENCES office_sheets(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS office_cell_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sheet_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    cell_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    author TEXT DEFAULT 'assistant',
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_office_sheets_wb ON office_sheets(workbook_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_office_revisions_sheet ON office_cell_revisions(sheet_id, revision_id)")
            conn.commit()

    # -------------------------------------------------------------------------
    # WORKBOOK & SHEET LIFECYCLE
    # -------------------------------------------------------------------------

    def create_workbook(
        self,
        title: str,
        description: Optional[str] = None,
        initial_sheet_names: Optional[List[str]] = None,
    ) -> WorkbookRecord:
        """Creates a new multi-sheet workbook."""
        wb_id = f"wb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{title[:12].strip().lower().replace(' ', '_')}"
        now = utc_now_iso()
        sheets = initial_sheet_names or ["Sheet1"]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO office_workbooks (id, title, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wb_id, title, description or "", now, now))

            sheet_records = []
            for idx, sname in enumerate(sheets):
                s_id = f"{wb_id}_s{idx + 1}"
                cursor.execute("""
                    INSERT INTO office_sheets (id, workbook_id, name, created_at)
                    VALUES (?, ?, ?, ?)
                """, (s_id, wb_id, sname, now))
                sheet_records.append(SheetRecord(id=s_id, workbook_id=wb_id, name=sname, created_at=now))
            conn.commit()

        return WorkbookRecord(
            id=wb_id,
            title=title,
            description=description,
            sheets=sheet_records,
            created_at=now,
            updated_at=now,
        )

    def list_workbooks(self) -> List[WorkbookRecord]:
        """Lists all workbooks with their associated sheets."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM office_workbooks ORDER BY updated_at DESC")
            wb_rows = cursor.fetchall()
            workbooks = []
            for row in wb_rows:
                cursor.execute("SELECT * FROM office_sheets WHERE workbook_id = ? ORDER BY id ASC", (row["id"],))
                sheet_rows = cursor.fetchall()
                sheets = [SheetRecord(**dict(s)) for s in sheet_rows]
                wb = WorkbookRecord(**dict(row), sheets=sheets)
                workbooks.append(wb)
            return workbooks

    def get_sheet(self, sheet_id_or_name: str) -> Optional[SheetRecord]:
        """Resolves sheet record by ID or Name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM office_sheets WHERE id = ? OR name = ?", (sheet_id_or_name, sheet_id_or_name))
            row = cursor.fetchone()
            if row:
                return SheetRecord(**dict(row))
        return None

    # -------------------------------------------------------------------------
    # CELL OPERATIONS & FORMULA EVALUATION
    # -------------------------------------------------------------------------

    def get_cell_value(self, sheet_id: str, row_idx: int, col_idx: int) -> Optional[str]:
        """Retrieves raw or computed value of a specific cell."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT raw_value, computed_value FROM office_cells
                WHERE sheet_id = ? AND row_idx = ? AND col_idx = ?
            """, (sheet_id, row_idx, col_idx))
            row = cursor.fetchone()
            if row:
                return row["computed_value"] if row["computed_value"] is not None else row["raw_value"]
        return None

    def read_sheet_grid(
        self,
        sheet_id: str,
        range_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reads all cells in a sheet or within a designated range (e.g. 'A1:C10').
        Returns 2D grid and cell map.
        """
        target_coords = parse_range_notation(range_str) if range_str else None
        target_set = set(target_coords) if target_coords else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM office_cells WHERE sheet_id = ? ORDER BY row_idx ASC, col_idx ASC", (sheet_id,))
            rows = cursor.fetchall()

        cells_map: Dict[str, CellRecord] = {}
        max_r, max_c = 0, 0
        for r in rows:
            row_i, col_i = r["row_idx"], r["col_idx"]
            if target_set and (row_i, col_i) not in target_set:
                continue
            c_name = coords_to_cell_name(row_i, col_i)
            rec = CellRecord(
                row_idx=row_i,
                col_idx=col_i,
                cell_name=c_name,
                raw_value=r["raw_value"] or "",
                computed_value=r["computed_value"],
                formula=r["formula"],
                data_type=r["data_type"],
            )
            cells_map[c_name] = rec
            if row_i > max_r:
                max_r = row_i
            if col_i > max_c:
                max_c = col_i

        # Format 2D array matrix
        matrix = []
        for r in range(max_r + 1):
            row_vals = []
            for c in range(max_c + 1):
                name = coords_to_cell_name(r, c)
                if name in cells_map:
                    val = cells_map[name].computed_value
                    row_vals.append(val if val is not None else cells_map[name].raw_value)
                else:
                    row_vals.append("")
            matrix.append(row_vals)

        return {
            "sheet_id": sheet_id,
            "range": range_str,
            "total_cells": len(cells_map),
            "cells": {k: v.model_dump() for k, v in cells_map.items()},
            "matrix": matrix,
        }

    def update_cells(
        self,
        sheet_id: str,
        cell_updates: Dict[str, Any],  # {"A1": "Revenue", "B1": 15000, "C1": "=B1*0.20"}
        author: str = "assistant",
    ) -> Dict[str, Any]:
        """
        Updates a batch of cells with Git-style revision tracking.
        Automatically evaluates formulas.
        """
        rev_id = f"rev_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        now = utc_now_iso()

        # Cell getter for formula evaluator
        sheet_cells_cache = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT row_idx, col_idx, raw_value, computed_value FROM office_cells WHERE sheet_id = ?", (sheet_id,))
            for r in cursor.fetchall():
                val = r["computed_value"] if r["computed_value"] is not None else r["raw_value"]
                sheet_cells_cache[(r["row_idx"], r["col_idx"])] = val

        # Overlay new updates
        for cell_name, raw_val in cell_updates.items():
            r, c = cell_name_to_coords(cell_name)
            sheet_cells_cache[(r, c)] = str(raw_val)

        evaluator = FormulaEvaluator(lambda r, c: sheet_cells_cache.get((r, c)))

        revisions: List[CellRevisionRecord] = []
        updated_cells: List[CellRecord] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for cell_name, raw_val in cell_updates.items():
                r, c = cell_name_to_coords(cell_name)
                str_val = str(raw_val)
                is_formula = str_val.startswith("=")
                formula = str_val if is_formula else None
                computed = str(evaluator.evaluate(str_val)) if is_formula else str_val

                # Get old value for git-style revision diff
                cursor.execute("""
                    SELECT raw_value FROM office_cells
                    WHERE sheet_id = ? AND row_idx = ? AND col_idx = ?
                """, (sheet_id, r, c))
                old_row = cursor.fetchone()
                old_val = old_row["raw_value"] if old_row else None

                # Determine data type
                dtype = "formula" if is_formula else ("number" if self._is_number(computed) else "string")

                # Upsert into office_cells
                cursor.execute("""
                    INSERT INTO office_cells (sheet_id, row_idx, col_idx, raw_value, computed_value, formula, data_type, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sheet_id, row_idx, col_idx) DO UPDATE SET
                        raw_value = excluded.raw_value,
                        computed_value = excluded.computed_value,
                        formula = excluded.formula,
                        data_type = excluded.data_type,
                        updated_at = excluded.updated_at
                """, (sheet_id, r, c, str_val, computed, formula, dtype, now))

                # Log revision
                cursor.execute("""
                    INSERT INTO office_cell_revisions (sheet_id, revision_id, cell_name, old_value, new_value, author, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sheet_id, rev_id, cell_name, old_val, str_val, author, now))

                revisions.append(CellRevisionRecord(
                    sheet_id=sheet_id,
                    revision_id=rev_id,
                    cell_name=cell_name,
                    old_value=old_val,
                    new_value=str_val,
                    author=author,
                    created_at=now,
                ))
                updated_cells.append(CellRecord(
                    row_idx=r,
                    col_idx=c,
                    cell_name=cell_name,
                    raw_value=str_val,
                    computed_value=computed,
                    formula=formula,
                    data_type=dtype,
                ))

            # Update workbook updated_at
            cursor.execute("""
                UPDATE office_workbooks SET updated_at = ?
                WHERE id = (SELECT workbook_id FROM office_sheets WHERE id = ?)
            """, (now, sheet_id))
            conn.commit()

        return {
            "status": "applied",
            "sheet_id": sheet_id,
            "revision_id": rev_id,
            "modified_cells": len(updated_cells),
            "revisions": [r.model_dump() for r in revisions],
        }

    def rollback_revision(self, sheet_id: str, revision_id: str) -> Dict[str, Any]:
        """Rolls back all cell mutations committed in a specific revision."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM office_cell_revisions
                WHERE sheet_id = ? AND revision_id = ?
            """, (sheet_id, revision_id))
            rows = cursor.fetchall()
            if not rows:
                return {"status": "not_found", "message": f"Revision {revision_id} not found on sheet {sheet_id}"}

            rollback_updates = {}
            for r in rows:
                c_name = r["cell_name"]
                old_v = r["old_value"]
                rollback_updates[c_name] = old_v if old_v is not None else ""

        # Apply the old values as a new rollback commit
        result = self.update_cells(sheet_id=sheet_id, cell_updates=rollback_updates, author="rollback_engine")
        result["reverted_revision_id"] = revision_id
        return result

    def get_sheet_revisions(self, sheet_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves revision history for a sheet."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT revision_id, author, created_at, COUNT(*) as changes_count
                FROM office_cell_revisions
                WHERE sheet_id = ?
                GROUP BY revision_id, author, created_at
                ORDER BY id DESC LIMIT ?
            """, (sheet_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # IMPORT & EXPORT (CSV, JSON, MARKDOWN)
    # -------------------------------------------------------------------------

    def import_csv(
        self,
        sheet_id: str,
        csv_text_or_path: str,
        has_headers: bool = True,
        author: str = "csv_importer",
    ) -> Dict[str, Any]:
        """Imports CSV tabular data into a designated sheet."""
        if "\n" in csv_text_or_path or "," in csv_text_or_path:
            lines = csv_text_or_path.strip().splitlines()
            reader = csv.reader(lines)
        else:
            file_path = Path(csv_text_or_path)
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_text_or_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))

        updates = {}
        for r_idx, row in enumerate(reader):
            for c_idx, val in enumerate(row):
                cell_name = coords_to_cell_name(r_idx, c_idx)
                updates[cell_name] = val.strip()

        return self.update_cells(sheet_id=sheet_id, cell_updates=updates, author=author)

    def export_csv(self, sheet_id: str) -> str:
        """Exports sheet data to CSV format."""
        grid = self.read_sheet_grid(sheet_id)
        matrix = grid["matrix"]
        output = []
        for row in matrix:
            output.append(",".join(f'"{v}"' if "," in str(v) else str(v) for v in row))
        return "\n".join(output)

    def export_markdown_table(
        self,
        sheet_id: str,
        range_str: Optional[str] = None,
        save_to_vault: bool = False,
        vault_note_name: Optional[str] = None,
    ) -> str:
        """
        Exports sheet contents to clean GitHub/Obsidian-compatible Markdown table format.
        Optionally saves to Obsidian vault note.
        """
        grid = self.read_sheet_grid(sheet_id, range_str=range_str)
        matrix = grid["matrix"]
        if not matrix or not any(matrix):
            return "| Empty Sheet |\n|---|\n| No data |"

        # Headers from row 0
        header_row = matrix[0]
        col_count = len(header_row)

        lines = []
        header_line = "| " + " | ".join(str(h) if h != "" else f"Col {i+1}" for i, h in enumerate(header_row)) + " |"
        sep_line = "| " + " | ".join("---" for _ in range(col_count)) + " |"
        lines.append(header_line)
        lines.append(sep_line)

        for row in matrix[1:]:
            padded = row + [""] * (col_count - len(row))
            data_line = "| " + " | ".join(str(cell).replace("|", "\\|") for cell in padded[:col_count]) + " |"
            lines.append(data_line)

        md_table = "\n".join(lines)

        if save_to_vault:
            note_title = vault_note_name or f"Spreadsheet Export - {sheet_id}"
            note_path = config.vault_dir / "02 - Knowledge" / f"{note_title}.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            content = f"# {note_title}\n\n*Exported by MaxIM Office Harness at {utc_now_iso()}*\n\n{md_table}\n"
            note_path.write_text(content, encoding="utf-8")
            logger.info(f"Saved spreadsheet Markdown table to vault: {note_path}")

        return md_table

    @staticmethod
    def _is_number(val: Any) -> bool:
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

# Global singleton
office_harness = OfficeHarnessEngine()
