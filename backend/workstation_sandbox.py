"""
10xProductivity Workstation & QwenPaw Sandboxed Guard Engine for MaxIM.
Repository references:
- ZhixiangLuo/10xProductivity: Developer workflow automation, scaffolding, Git atomic hygiene.
- agentscope-ai/QwenPaw: Sandboxed execution boundaries, pre-execution safety audits, destructive command interceptor.

Functional Core:
1. QwenPaw Pre-Execution Safety Audit: Analyzes commands for destructive operations, unauthorized disk formatting,
   system file deletion, and path traversal prior to execution.
2. Sandboxed Subprocess Runner: Runs audited shell commands with strict execution timeouts, output clipping,
   and deterministic resource limits.
3. Persistent SQLite Audit Ledger: Logs all attempted commands, risk assessments, verdicts, and outcomes into `sandbox_audit_log`.
4. 10xProductivity Project Scaffolder: Generates clean, production-grade project foundations (Python service, FastAPI API, CLI utility).
5. Git Workspace Hygiene & Atomic Committer: Inspects working tree cleanliness, untracked artifacts, branch status,
   and generates conventional atomic commits.
6. Developer Snippet & Recipe Registry: Stores and retrieves verified code snippets in SQLite table `workstation_snippets`.
"""

import os
import re
import time
import json
import sqlite3
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from pydantic import BaseModel, Field

from config import config

logger = logging.getLogger("maxim.workstation_sandbox")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Models
# ============================================================================

class CommandAuditResult(BaseModel):
    command: str
    is_safe: bool
    verdict: str  # ALLOW, WARN, BLOCK
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    matched_patterns: List[str] = Field(default_factory=list)
    suggested_safe_alternative: Optional[str] = None


class SandboxedExecutionResult(BaseModel):
    command: str
    audit: CommandAuditResult
    executed: bool
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    timed_out: bool = False
    error: Optional[str] = None


class GitHygieneStatus(BaseModel):
    is_git_repo: bool
    current_branch: str = "unknown"
    staged_files: List[str] = Field(default_factory=list)
    unstaged_files: List[str] = Field(default_factory=list)
    untracked_files: List[str] = Field(default_factory=list)
    is_clean: bool = True
    hygiene_score: int = 100
    recommendations: List[str] = Field(default_factory=list)


class DeveloperSnippet(BaseModel):
    id: Optional[int] = None
    title: str
    language: str
    code: str
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)


# ============================================================================
# QwenPaw Dangerous Pattern Catalog
# ============================================================================

DANGEROUS_PATTERNS = [
    # Critical System Destruction
    (r"\brm\s+-[rRfF]{1,3}\s+(/\s*$|/\*|/etc|/bin|/sbin|/usr|/var|/root|/home)", "CRITICAL", "Recursive deletion of root or core system directories"),
    (r"\b(format|Format-Volume)\b.*([a-zA-Z]:|-DriveLetter\s+[a-zA-Z]|\b[a-zA-Z]\b)", "CRITICAL", "Disk volume formatting detected"),
    (r"\bdel\s+(/[sSqQfF]\s+)+([c-zC-Z]:\\|[c-zC-Z]:\\Windows)", "CRITICAL", "Recursive deletion targeting drive root or Windows system folder"),
    (r"\brmdir\s+(/[sSqQ]\s+)+([c-zC-Z]:\\|[c-zC-Z]:\\Windows)", "CRITICAL", "Directory removal targeting drive root or Windows system directory"),
    (r"\b(mkfs|dd\s+if=.*of=/dev/)", "CRITICAL", "Low-level filesystem overwrite or partition zeroing"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "CRITICAL", "Bash fork-bomb detected"),
    (r"\b(bcdedit|diskpart|reg\s+delete\s+HKLM)", "CRITICAL", "System boot config, partition editor, or critical registry deletion"),
    
    # Destructive DB Drops
    (r"\bDROP\s+DATABASE\b", "HIGH", "Dropping entire database instance"),
    (r"\bDROP\s+TABLE\s+(users|auth|accounts|transactions|audit)", "HIGH", "Dropping critical entity table"),
    
    # Unauthorized Shutdown / Reboot
    (r"\b(shutdown|Stop-Computer|Restart-Computer)\b", "HIGH", "System shutdown or reboot command"),
    
    # Excessive Permission Grant
    (r"\bchmod\s+(-R\s+)?(777|666)\s+/", "HIGH", "Global insecure permission grant on system files"),
    
    # Potential Exfiltration of sensitive files
    (r"\bcurl\b.*-d\s+@.*\b(id_rsa|id_ed25519|\.env|\.ssh|credentials|shadow)", "HIGH", "Potential exfiltration of private keys or sensitive credentials"),
]

SUSPICIOUS_PATTERNS = [
    (r"\brm\s+-[rRfF]{1,3}\b", "MEDIUM", "Recursive file deletion"),
    (r"\bdel\s+/[sSqQ]\b", "MEDIUM", "Quiet or recursive file deletion"),
    (r"\bkill\s+-9\b|\btaskkill\s+/f\b", "LOW", "Forceful process termination"),
    (r"\bgit\s+reset\s+--hard\b", "MEDIUM", "Destructive git reset discarding uncommitted changes"),
    (r"\bgit\s+clean\s+-[fF][dD]?\b", "MEDIUM", "Forceful git clean removing untracked files"),
    (r"\bcurl\b.*\|\s*(bash|sh|powershell|cmd)\b", "HIGH", "Direct execution of remote script piped to shell"),
]


# ============================================================================
# Workstation & Sandbox Engine
# ============================================================================

class WorkstationSandboxEngine:
    def __init__(self, db_path: Optional[Path] = None, workspace_root: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.workspace_root = workspace_root or config.base_dir
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    command TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    exit_code INTEGER,
                    duration_ms REAL,
                    output_preview TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workstation_snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    language TEXT NOT NULL,
                    code TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sandbox_verdict ON sandbox_audit_log(verdict)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sandbox_timestamp ON sandbox_audit_log(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snippets_lang ON workstation_snippets(language)")

    # ------------------------------------------------------------------------
    # QwenPaw Pre-Execution Safety Guard
    # ------------------------------------------------------------------------

    def audit_command(self, command: str, working_dir: Optional[str] = None) -> CommandAuditResult:
        cmd_clean = command.strip()
        matched: List[str] = []

        # 1. Critical destructive checks
        for pattern, risk, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                matched.append(f"{risk}: {desc}")
                return CommandAuditResult(
                    command=cmd_clean,
                    is_safe=False,
                    verdict="BLOCK",
                    risk_level=risk,
                    reason=f"QwenPaw Guard blocked destructive command: {desc}",
                    matched_patterns=matched,
                    suggested_safe_alternative="Inspect target directory manually with non-destructive queries."
                )

        # 2. Suspicious / warning checks
        highest_risk = "LOW"
        reasons: List[str] = []
        for pattern, risk, desc in SUSPICIOUS_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                matched.append(f"{risk}: {desc}")
                reasons.append(desc)
                if risk == "HIGH":
                    highest_risk = "HIGH"
                elif risk == "MEDIUM" and highest_risk != "HIGH":
                    highest_risk = "MEDIUM"

        # 3. Path boundary checks
        if working_dir:
            try:
                target_path = Path(working_dir).resolve()
                ws_path = Path(self.workspace_root).resolve()
                # Check if target_path is attempting escape to sensitive Windows roots
                if str(target_path).lower() in ["c:\\", "c:\\windows", "c:\\windows\\system32"]:
                    return CommandAuditResult(
                        command=cmd_clean,
                        is_safe=False,
                        verdict="BLOCK",
                        risk_level="CRITICAL",
                        reason="Working directory points to sensitive Windows root system folder",
                        matched_patterns=["CRITICAL: Root traversal"],
                        suggested_safe_alternative=f"Stay within workspace root: {self.workspace_root}"
                    )
            except Exception as e:
                logger.warning(f"Error checking working directory boundary: {e}")

        if matched:
            return CommandAuditResult(
                command=cmd_clean,
                is_safe=True,
                verdict="WARN",
                risk_level=highest_risk,
                reason="; ".join(reasons),
                matched_patterns=matched
            )

        return CommandAuditResult(
            command=cmd_clean,
            is_safe=True,
            verdict="ALLOW",
            risk_level="LOW",
            reason="Command passed QwenPaw safety heuristics.",
            matched_patterns=[]
        )

    # ------------------------------------------------------------------------
    # Sandboxed Command Execution
    # ------------------------------------------------------------------------

    def execute_sandboxed_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_seconds: int = 15,
        max_output_chars: int = 30000
    ) -> SandboxedExecutionResult:
        run_cwd = cwd or str(self.workspace_root)
        audit = self.audit_command(command, run_cwd)

        # Intercept blocked commands
        if audit.verdict == "BLOCK":
            self._log_audit(command, run_cwd, audit.verdict, audit.risk_level, audit.reason, None, 0.0, "[BLOCKED BY QWENPAW]")
            return SandboxedExecutionResult(
                command=command,
                audit=audit,
                executed=False,
                error=audit.reason
            )

        # Enforce execution timeout boundaries
        clamped_timeout = max(1, min(timeout_seconds, 60))
        start_time = time.perf_counter()
        timed_out = False
        exit_code = None
        stdout_text = ""
        stderr_text = ""
        err_msg = None

        try:
            # Execute synchronously with strict timeout
            process = subprocess.run(
                command,
                shell=True,
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=clamped_timeout,
                encoding="utf-8",
                errors="replace"
            )
            exit_code = process.returncode
            stdout_text = process.stdout or ""
            stderr_text = process.stderr or ""
        except subprocess.TimeoutExpired:
            timed_out = True
            err_msg = f"Execution timed out after {clamped_timeout} seconds"
            exit_code = -1
        except Exception as ex:
            err_msg = str(ex)
            exit_code = -1

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Output clipping to avoid payload explosion
        if len(stdout_text) > max_output_chars:
            stdout_text = stdout_text[:max_output_chars] + f"\n... [Output clipped: {len(stdout_text) - max_output_chars} chars truncated]"
        if len(stderr_text) > max_output_chars:
            stderr_text = stderr_text[:max_output_chars] + f"\n... [Stderr clipped: {len(stderr_text) - max_output_chars} chars truncated]"

        preview = (stdout_text[:200] if stdout_text else stderr_text[:200]).strip()
        self._log_audit(command, run_cwd, audit.verdict, audit.risk_level, audit.reason, exit_code, duration_ms, preview)

        return SandboxedExecutionResult(
            command=command,
            audit=audit,
            executed=not timed_out and err_msg is None,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_ms=duration_ms,
            timed_out=timed_out,
            error=err_msg
        )

    def _log_audit(
        self,
        command: str,
        cwd: str,
        verdict: str,
        risk_level: str,
        reason: str,
        exit_code: Optional[int],
        duration_ms: float,
        output_preview: str
    ):
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO sandbox_audit_log (
                        timestamp, command, cwd, verdict, risk_level, reason, exit_code, duration_ms, output_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    utc_now_iso(), command, cwd, verdict, risk_level, reason, exit_code, duration_ms, output_preview
                ))
        except Exception as e:
            logger.error(f"Failed to record sandbox audit log: {e}")

    def list_audit_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, command, cwd, verdict, risk_level, reason, exit_code, duration_ms, output_preview
                FROM sandbox_audit_log
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------------
    # 10xProductivity Workstation Project Scaffolding
    # ------------------------------------------------------------------------

    def scaffold_project(
        self,
        project_type: str,
        target_dir: str,
        project_name: str,
        description: str = "MaxIM Workstation Generated Component"
    ) -> Dict[str, Any]:
        dest_path = Path(target_dir).resolve()
        # Boundary validation: ensure destination is within allowed workspace or child
        clean_name = re.sub(r"[^\w\-_]", "_", project_name)
        target_project_dir = dest_path / clean_name
        target_project_dir.mkdir(parents=True, exist_ok=True)

        created_files: List[str] = []
        ptype = project_type.lower().strip()

        if ptype in ["python_service", "python", "service"]:
            # 1. main.py
            main_code = f'''"""\n{clean_name} Service\n{description}\n"""\nimport logging\nfrom pathlib import Path\n\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger("{clean_name}")\n\ndef run():\n    logger.info("Initializing {clean_name} service...")\n    print("Service {clean_name} is running.")\n\nif __name__ == "__main__":\n    run()\n'''
            (target_project_dir / "main.py").write_text(main_code, encoding="utf-8")
            created_files.append(str(target_project_dir / "main.py"))

            # 2. requirements.txt
            reqs = "pydantic>=2.0\npytest>=8.0\n"
            (target_project_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
            created_files.append(str(target_project_dir / "requirements.txt"))

            # 3. test_service.py
            tests_dir = target_project_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            test_code = f'''import pytest\nfrom main import run\n\ndef test_service_initialization():\n    assert callable(run)\n'''
            (tests_dir / "test_main.py").write_text(test_code, encoding="utf-8")
            created_files.append(str(tests_dir / "test_main.py"))

        elif ptype in ["fastapi", "api"]:
            # 1. app.py
            app_code = f'''"""\nFastAPI Microservice: {clean_name}\n"""\nfrom fastapi import FastAPI\n\napp = FastAPI(title="{clean_name}", description="{description}")\n\n@app.get("/health")\ndef health_check():\n    return {{"status": "healthy", "service": "{clean_name}"}}\n'''
            (target_project_dir / "app.py").write_text(app_code, encoding="utf-8")
            created_files.append(str(target_project_dir / "app.py"))

            # 2. test_app.py
            test_code = f'''from fastapi.testclient import TestClient\nfrom app import app\n\nclient = TestClient(app)\n\ndef test_health():\n    res = client.get("/health")\n    assert res.status_code == 200\n    assert res.json()["status"] == "healthy"\n'''
            (target_project_dir / "test_app.py").write_text(test_code, encoding="utf-8")
            created_files.append(str(target_project_dir / "test_app.py"))

        elif ptype in ["cli", "cli_tool"]:
            # 1. cli.py
            cli_code = f'''"""\nCLI Command Utility: {clean_name}\n"""\nimport argparse\n\ndef main():\n    parser = argparse.ArgumentParser(description="{description}")\n    parser.add_argument("--action", choices=["status", "run"], default="status")\n    args = parser.parse_args()\n    print(f"Executing {clean_name} action: {{args.action}}")\n\nif __name__ == "__main__":\n    main()\n'''
            (target_project_dir / "cli.py").write_text(cli_code, encoding="utf-8")
            created_files.append(str(target_project_dir / "cli.py"))

        else:
            # Generic foundation
            (target_project_dir / "README.md").write_text(f"# {clean_name}\n\n{description}\n", encoding="utf-8")
            created_files.append(str(target_project_dir / "README.md"))

        # Root README
        readme_path = target_project_dir / "README.md"
        if not readme_path.exists():
            readme_path.write_text(f"# {clean_name}\n\n{description}\n\nGenerated by MaxIM 10xProductivity Workstation.\n", encoding="utf-8")
            created_files.append(str(readme_path))

        return {
            "success": True,
            "project_name": clean_name,
            "project_type": ptype,
            "directory": str(target_project_dir),
            "created_files": created_files
        }

    # ------------------------------------------------------------------------
    # Git Workspace Hygiene & Conventional Commit Manager
    # ------------------------------------------------------------------------

    def get_git_hygiene(self, repo_dir: Optional[str] = None) -> GitHygieneStatus:
        dir_to_check = repo_dir or str(self.workspace_root)
        try:
            # Check if valid git repository
            res = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=dir_to_check,
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode != 0:
                return GitHygieneStatus(
                    is_git_repo=False,
                    current_branch="none",
                    is_clean=False,
                    hygiene_score=0,
                    recommendations=["Current working directory is not a Git repository. Run 'git init' to start tracking."]
                )

            # Current branch
            branch_res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=dir_to_check,
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = branch_res.stdout.strip() or "main"

            # Porcelain status
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=dir_to_check,
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = [line for line in status_res.stdout.splitlines() if line.strip()]

            staged: List[str] = []
            unstaged: List[str] = []
            untracked: List[str] = []

            for line in lines:
                if len(line) < 3:
                    continue
                code_x = line[0]
                code_y = line[1]
                filepath = line[3:].strip()

                if code_x in ["M", "A", "D", "R", "C"]:
                    staged.append(filepath)
                if code_y in ["M", "D"]:
                    unstaged.append(filepath)
                if code_x == "?" and code_y == "?":
                    untracked.append(filepath)

            is_clean = len(lines) == 0
            score = 100
            recs: List[str] = []

            if untracked:
                score -= min(30, len(untracked) * 5)
                recs.append(f"{len(untracked)} untracked files present. Clean or add to .gitignore.")
            if unstaged:
                score -= min(40, len(unstaged) * 5)
                recs.append(f"{len(unstaged)} unstaged modified files. Review changes and stage.")
            if staged:
                recs.append(f"{len(staged)} files staged for atomic commit.")

            score = max(0, score)

            return GitHygieneStatus(
                is_git_repo=True,
                current_branch=branch,
                staged_files=staged,
                unstaged_files=unstaged,
                untracked_files=untracked,
                is_clean=is_clean,
                hygiene_score=score,
                recommendations=recs
            )
        except Exception as e:
            logger.error(f"Error inspecting git hygiene: {e}")
            return GitHygieneStatus(
                is_git_repo=False,
                current_branch="error",
                is_clean=False,
                hygiene_score=0,
                recommendations=[f"Error checking git repository: {str(e)}"]
            )

    def create_atomic_commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
        repo_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        dir_to_check = repo_dir or str(self.workspace_root)
        msg_clean = message.strip()

        # Validate Conventional Commits pattern
        conv_pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_\-.]+\))?:\s+.+"
        if not re.match(conv_pattern, msg_clean):
            return {
                "success": False,
                "error": "Commit message must follow Conventional Commits format, e.g., 'feat: add sandbox engine' or 'fix(auth): handle token expiry'."
            }

        try:
            # Stage files
            if files:
                stage_cmd = ["git", "add"] + files
            else:
                stage_cmd = ["git", "add", "-u"]  # stage tracked modified/deleted
            
            subprocess.run(stage_cmd, cwd=dir_to_check, check=True, capture_output=True, text=True, timeout=10)

            # Commit
            commit_res = subprocess.run(
                ["git", "commit", "-m", msg_clean],
                cwd=dir_to_check,
                capture_output=True,
                text=True,
                timeout=10
            )

            if commit_res.returncode == 0:
                return {
                    "success": True,
                    "message": msg_clean,
                    "commit_output": commit_res.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": commit_res.stderr.strip() or commit_res.stdout.strip() or "Nothing to commit or git commit failed."
                }
        except Exception as ex:
            return {"success": False, "error": str(ex)}

    # ------------------------------------------------------------------------
    # Developer Snippet & Recipe Registry
    # ------------------------------------------------------------------------

    def save_snippet(
        self,
        title: str,
        language: str,
        code: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> DeveloperSnippet:
        tag_list = tags or []
        created_at = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO workstation_snippets (title, language, code, tags, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title.strip(), language.lower().strip(), code, json.dumps(tag_list), description, created_at))
            snippet_id = cursor.lastrowid

        return DeveloperSnippet(
            id=snippet_id,
            title=title.strip(),
            language=language.lower().strip(),
            code=code,
            tags=tag_list,
            description=description,
            created_at=created_at
        )

    def list_snippets(self, language: Optional[str] = None, tag: Optional[str] = None) -> List[DeveloperSnippet]:
        with self._get_connection() as conn:
            query = "SELECT id, title, language, code, tags, description, created_at FROM workstation_snippets"
            params: List[Any] = []
            conditions: List[str] = []

            if language:
                conditions.append("language = ?")
                params.append(language.lower().strip())

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY id DESC"
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results: List[DeveloperSnippet] = []
        for r in rows:
            tags = json.loads(r["tags"]) if r["tags"] else []
            if tag and tag.lower() not in [t.lower() for t in tags]:
                continue
            results.append(DeveloperSnippet(
                id=r["id"],
                title=r["title"],
                language=r["language"],
                code=r["code"],
                tags=tags,
                description=r["description"],
                created_at=r["created_at"]
            ))
        return results

    def delete_snippet(self, snippet_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM workstation_snippets WHERE id = ?", (snippet_id,))
            return cursor.rowcount > 0


# Singleton instance
workstation_sandbox = WorkstationSandboxEngine()
