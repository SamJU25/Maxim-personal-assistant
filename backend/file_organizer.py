"""
File & Directory Organizer Engine for MaxIM.
Provides safe, category-based file organization with dry-run previews,
collision protection, and SQLite transaction logging with full undo rollback.

Default Categories:
- Photos: .png, .jpg, .jpeg, .gif, .webp, .svg, .bmp, .ico, .tiff
- Documents: .pdf, .docx, .doc, .txt, .xlsx, .pptx, .csv, .md, .epub, .odt
- Videos: .mp4, .mkv, .mov, .avi, .webm, .flv, .wmv
- Audio: .mp3, .wav, .m4a, .flac, .aac, .ogg
- Archives: .zip, .tar, .gz, .rar, .7z, .bz2
- Installers: .exe, .msi, .dmg, .pkg, .iso
- Code: .py, .js, .ts, .tsx, .jsx, .html, .css, .json, .yaml, .yml, .sql
"""
import os
import shutil
import sqlite3
import logging
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.file_organizer")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT_CATEGORY_EXTENSIONS: Dict[str, List[str]] = {
    "Photos": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv", ".md", ".epub", ".odt"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv"],
    "Audio": [".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"],
    "Installers": [".exe", ".msi", ".dmg", ".pkg", ".iso"],
    "Code": [".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".yaml", ".yml", ".sql"],
}

SYSTEM_IGNORED_EXTENSIONS = {".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite3", ".tmp", ".crdownload", ".part", ".lock"}
SYSTEM_IGNORED_FILENAMES = {"desktop.ini", "thumbs.db", ".ds_store"}

class PlannedFileMove(BaseModel):
    file_name: str
    original_path: str
    destination_folder: str
    destination_path: str
    category: str
    file_size_bytes: int

class DirectoryScanResult(BaseModel):
    directory: str
    total_files: int
    total_size_bytes: int
    category_counts: Dict[str, int]
    category_sizes: Dict[str, int]
    planned_moves: List[PlannedFileMove] = Field(default_factory=list)
    ignored_items: List[str] = Field(default_factory=list)

class OrganizationResult(BaseModel):
    batch_id: str
    directory: str
    is_dry_run: bool
    moved_count: int
    failed_count: int
    moves: List[PlannedFileMove]
    errors: List[Dict[str, str]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=utc_now_iso)

class FileOrganizerService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(config.backend_dir / "maxim.db")
        self.category_extensions = DEFAULT_CATEGORY_EXTENSIONS.copy()
        self._init_sqlite()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_sqlite(self):
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_organization_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL,
                        directory TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        original_path TEXT NOT NULL,
                        destination_path TEXT NOT NULL,
                        category TEXT NOT NULL,
                        file_size_bytes INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL -- moved, undone, failed
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_file_org_batch ON file_organization_history(batch_id);")
                conn.commit()
        except Exception as e:
            logger.error("Failed to initialize file organization SQLite tables: %s", e)

    def _get_category_for_extension(self, ext: str) -> Optional[str]:
        ext_lower = ext.lower()
        for cat, ext_list in self.category_extensions.items():
            if ext_lower in ext_list:
                return cat
        return None

    def _resolve_unique_destination(self, dest_folder: Path, file_name: str) -> Path:
        """Avoids file overwrites by appending a sequential number if target exists."""
        target = dest_folder / file_name
        if not target.exists():
            return target

        stem = Path(file_name).stem
        suffix = Path(file_name).suffix
        counter = 1
        while target.exists():
            target = dest_folder / f"{stem} ({counter}){suffix}"
            counter += 1
        return target

    def scan_directory(
        self,
        directory_path: str,
        custom_categories: Optional[Dict[str, List[str]]] = None,
    ) -> DirectoryScanResult:
        """
        Scans a directory and generates a category breakdown and organization plan
        without making any changes to disk.
        """
        dir_p = Path(os.path.expanduser(os.path.expandvars(directory_path))).resolve()
        if not dir_p.exists() or not dir_p.is_dir():
            return DirectoryScanResult(
                directory=str(dir_p),
                total_files=0,
                total_size_bytes=0,
                category_counts={},
                category_sizes={},
                ignored_items=[f"Directory '{directory_path}' does not exist or is not a directory."],
            )

        cat_map = custom_categories or self.category_extensions
        category_counts: Dict[str, int] = {}
        category_sizes: Dict[str, int] = {}
        planned_moves: List[PlannedFileMove] = []
        ignored_items: List[str] = []
        total_size = 0
        total_files = 0

        # Known category folder names to avoid moving them into themselves
        category_folder_names = set(cat_map.keys())

        try:
            for item in dir_p.iterdir():
                # Skip subdirectories (e.g. existing Photos/, Documents/ folders or internal dirs)
                if item.is_dir():
                    ignored_items.append(f"Directory: {item.name}")
                    continue

                if not item.is_file():
                    continue

                # Skip hidden files, databases, lockfiles, and in-progress downloads
                if item.name.startswith(".") or item.suffix.lower() in SYSTEM_IGNORED_EXTENSIONS or item.name.lower() in SYSTEM_IGNORED_FILENAMES:
                    ignored_items.append(f"System/Temp: {item.name}")
                    continue

                total_files += 1
                try:
                    fsize = item.stat().st_size
                except Exception:
                    fsize = 0
                total_size += fsize

                ext = item.suffix.lower()
                matched_category: Optional[str] = None
                for cat, ext_list in cat_map.items():
                    if ext in [e.lower() for e in ext_list]:
                        matched_category = cat
                        break

                if not matched_category:
                    matched_category = "Other"

                category_counts[matched_category] = category_counts.get(matched_category, 0) + 1
                category_sizes[matched_category] = category_sizes.get(matched_category, 0) + fsize

                dest_folder = dir_p / matched_category
                dest_file = self._resolve_unique_destination(dest_folder, item.name)

                planned_moves.append(PlannedFileMove(
                    file_name=item.name,
                    original_path=str(item),
                    destination_folder=str(dest_folder),
                    destination_path=str(dest_file),
                    category=matched_category,
                    file_size_bytes=fsize,
                ))
        except Exception as e:
            ignored_items.append(f"Scan error: {str(e)}")

        return DirectoryScanResult(
            directory=str(dir_p),
            total_files=total_files,
            total_size_bytes=total_size,
            category_counts=category_counts,
            category_sizes=category_sizes,
            planned_moves=planned_moves,
            ignored_items=ignored_items,
        )

    def organize_directory(
        self,
        directory_path: str,
        dry_run: bool = False,
        custom_categories: Optional[Dict[str, List[str]]] = None,
    ) -> OrganizationResult:
        """
        Organizes files into category folders.
        If dry_run=True, returns the proposed moves without relocating files.
        If dry_run=False, moves the files and records transactions in SQLite for rollback.
        """
        scan = self.scan_directory(directory_path, custom_categories=custom_categories)
        batch_id = f"batch_{uuid.uuid4().hex[:10]}"

        if dry_run:
            return OrganizationResult(
                batch_id=batch_id,
                directory=scan.directory,
                is_dry_run=True,
                moved_count=len(scan.planned_moves),
                failed_count=0,
                moves=scan.planned_moves,
            )

        executed_moves: List[PlannedFileMove] = []
        errors: List[Dict[str, str]] = []

        with self._get_connection() as conn:
            for move in scan.planned_moves:
                try:
                    src = Path(move.original_path)
                    dest_folder = Path(move.destination_folder)
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    
                    # Re-resolve destination at execution time in case of conflicts
                    final_dest = self._resolve_unique_destination(dest_folder, move.file_name)
                    shutil.move(str(src), str(final_dest))

                    move.destination_path = str(final_dest)
                    executed_moves.append(move)

                    # Log to SQLite
                    conn.execute("""
                        INSERT INTO file_organization_history
                        (batch_id, directory, file_name, original_path, destination_path, category, file_size_bytes, timestamp, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'moved')
                    """, (batch_id, scan.directory, move.file_name, move.original_path, str(final_dest), move.category, move.file_size_bytes, utc_now_iso()))
                except Exception as e:
                    errors.append({"file": move.file_name, "error": str(e)})
                    conn.execute("""
                        INSERT INTO file_organization_history
                        (batch_id, directory, file_name, original_path, destination_path, category, file_size_bytes, timestamp, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'failed')
                    """, (batch_id, scan.directory, move.file_name, move.original_path, move.destination_path, move.category, move.file_size_bytes, utc_now_iso()))

            conn.commit()

        return OrganizationResult(
            batch_id=batch_id,
            directory=scan.directory,
            is_dry_run=False,
            moved_count=len(executed_moves),
            failed_count=len(errors),
            moves=executed_moves,
            errors=errors,
        )

    def undo_organization(self, batch_id: str) -> Dict[str, Any]:
        """
        Reverts an organization batch by moving files back to their original locations.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM file_organization_history
                WHERE batch_id = ? AND status = 'moved'
            """, (batch_id,))
            rows = cursor.fetchall()

            if not rows:
                return {"status": "error", "error": f"No active moved files found for batch '{batch_id}'."}

            restored = []
            failed = []

            for row in rows:
                orig = Path(row["original_path"])
                current = Path(row["destination_path"])

                try:
                    if current.exists():
                        orig.parent.mkdir(parents=True, exist_ok=True)
                        dest = self._resolve_unique_destination(orig.parent, orig.name)
                        shutil.move(str(current), str(dest))
                        restored.append(row["file_name"])

                        conn.execute("""
                            UPDATE file_organization_history
                            SET status = 'undone'
                            WHERE id = ?
                        """, (row["id"],))
                    else:
                        failed.append({"file": row["file_name"], "reason": "File not found at destination."})
                except Exception as e:
                    failed.append({"file": row["file_name"], "reason": str(e)})

            conn.commit()

        return {
            "status": "success",
            "batch_id": batch_id,
            "restored_count": len(restored),
            "failed_count": len(failed),
            "restored_files": restored,
            "failed": failed,
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent organization batches and file records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT batch_id, directory, COUNT(*) as file_count, timestamp, status
                FROM file_organization_history
                GROUP BY batch_id, status
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

# Global Singleton
file_organizer = FileOrganizerService()
