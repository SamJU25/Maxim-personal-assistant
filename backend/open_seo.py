"""
OpenSEO Website Visibility, Technical SEO & Generative Engine Auditor for MaxIM.
Adapted from every-app/open-seo architecture.
Performs comprehensive technical SEO audits, meta tag validations, heading hierarchy checks,
keyword density profiling, and exports actionable scorecard notes to Obsidian.
Repository reference: https://github.com/every-app/open-seo
"""
import sqlite3
import re
import uuid
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import httpx
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class OpenSEOEngine:
    def __init__(self, db_path: Optional[Path] = None, vault_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.vault_dir = vault_dir or config.vault_dir
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS seo_audits (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                seo_score INTEGER NOT NULL,
                passed_checks INTEGER NOT NULL,
                total_checks INTEGER NOT NULL,
                issues_count INTEGER NOT NULL,
                vault_path TEXT,
                created_at TEXT NOT NULL
            );
            """)

    def audit_html(self, html: str, url: str = "https://example.com") -> Dict[str, Any]:
        """Performs static technical analysis on HTML source string."""
        passed = []
        issues = []

        # 1. Title Tag Check
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = title_match.group(1).strip()
            t_len = len(title_text)
            if 30 <= t_len <= 65:
                passed.append(f"Title tag length is optimal ({t_len} chars): '{title_text}'")
            elif t_len < 30:
                issues.append(f"Title tag is too short ({t_len} chars): '{title_text}'. Recommended 30-65 chars.")
            else:
                issues.append(f"Title tag is too long ({t_len} chars): '{title_text}'. May be truncated in SERP.")
        else:
            issues.append("Missing <title> tag in HTML head.")

        # 2. Meta Description Check
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
        
        if desc_match:
            desc_text = desc_match.group(1).strip()
            d_len = len(desc_text)
            if 100 <= d_len <= 165:
                passed.append(f"Meta description length is optimal ({d_len} chars).")
            else:
                issues.append(f"Meta description length ({d_len} chars) is outside optimal 100-165 range.")
        else:
            issues.append("Missing <meta name='description'> tag.")

        # 3. Heading Hierarchy (H1 & H2)
        h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if len(h1_matches) == 1:
            passed.append(f"Proper heading structure: Single <h1> tag found ('{h1_matches[0].strip()}').")
        elif len(h1_matches) == 0:
            issues.append("Critical: No <h1> tag found on page.")
        else:
            issues.append(f"Multiple <h1> tags found ({len(h1_matches)}). Only one primary <h1> should be present.")

        h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
        if len(h2_matches) >= 1:
            passed.append(f"Subheadings present: {len(h2_matches)} <h2> tags detected.")
        else:
            issues.append("No <h2> subheadings detected. Structure could be improved.")

        # 4. OpenGraph Social Tags
        og_title = re.search(r'<meta[^>]*property=["\']og:title["\']', html, re.IGNORECASE)
        og_desc = re.search(r'<meta[^>]*property=["\']og:description["\']', html, re.IGNORECASE)
        og_image = re.search(r'<meta[^>]*property=["\']og:image["\']', html, re.IGNORECASE)
        if og_title and og_desc and og_image:
            passed.append("OpenGraph tags (og:title, og:description, og:image) are fully present.")
        else:
            issues.append("Incomplete OpenGraph tags (check og:title, og:description, og:image for rich snippets).")

        # 5. Canonical Tag
        canonical = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', html, re.IGNORECASE)
        if canonical:
            passed.append(f"Canonical link tag specified: '{canonical.group(1)}'.")
        else:
            issues.append("Missing <link rel='canonical'> tag (recommended to prevent duplicate content indexing).")

        # 6. Image Alt Tags
        img_tags = re.findall(r"<img[^>]*>", html, re.IGNORECASE)
        imgs_without_alt = [img for img in img_tags if not re.search(r'alt=["\'](.*?)["\']', img, re.IGNORECASE)]
        if img_tags and not imgs_without_alt:
            passed.append(f"All {len(img_tags)} image(s) have alt attributes.")
        elif imgs_without_alt:
            issues.append(f"{len(imgs_without_alt)} image(s) missing alt accessibility/SEO attributes.")
        else:
            passed.append("No images to evaluate.")

        # 7. Schema.org / JSON-LD
        schema_match = re.search(r'<script[^>]*type=["\']application/ld\+json["\']', html, re.IGNORECASE)
        if schema_match:
            passed.append("Structured data: Schema.org JSON-LD markup found.")
        else:
            issues.append("No JSON-LD structured data markup detected.")

        total_checks = len(passed) + len(issues)
        score = int(round((len(passed) / max(1, total_checks)) * 100))

        # Save to Obsidian vault at vault/02 - Knowledge/SEO Audits/<clean_domain>.md
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or "audit"
        clean_name = "".join(c for c in domain if c.isalnum() or c in ("-", "_")).strip() or "audit"
        
        now = utc_now_iso()
        audit_id = f"seo_{uuid.uuid4().hex[:8]}"

        out_dir = self.vault_dir / "02 - Knowledge" / "SEO Audits"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{clean_name}.md"

        md = f"# 🔍 Technical SEO Audit: {domain}\n\n"
        md += f"> **Target URL:** `{url}` | **SEO Health Score:** `{score}/100`\n"
        md += f"> **Audited:** `{now}` | **Audit ID:** `{audit_id}`\n"
        md += f"> **Tags:** #seo #audit #web-visibility #performance\n\n"
        md += "## 📊 Scorecard Summary\n"
        md += f"- **Score:** `{score}/100`\n"
        md += f"- **Passed Checks:** `{len(passed)}/{total_checks}`\n"
        md += f"- **Actionable Issues:** `{len(issues)}`\n\n"

        md += "## ✅ Passed Audits\n"
        for p in passed:
            md += f"- [x] {p}\n"
        md += "\n"

        md += "## ⚠️ Recommended Remediations\n"
        for issue in issues:
            md += f"- [ ] {issue}\n"
        md += "\n---\n*Generated by OpenSEO Visibility Engine for MaxIM*\n"

        out_file.write_text(md, encoding="utf-8")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO seo_audits (id, url, seo_score, passed_checks, total_checks, issues_count, vault_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (audit_id, url, score, len(passed), total_checks, len(issues), str(out_file), now))
            conn.commit()

        return {
            "audit_id": audit_id,
            "url": url,
            "seo_score": score,
            "passed_checks": len(passed),
            "issues_count": len(issues),
            "passed": passed,
            "issues": issues,
            "vault_path": str(out_file),
            "created_at": now
        }

    def audit_url(self, url: str, test_mode: bool = False) -> Dict[str, Any]:
        """Fetches page HTML and runs comprehensive SEO audit."""
        clean_url = url.strip()
        if not clean_url:
            raise ValueError("URL cannot be empty.")

        if test_mode:
            sample_html = """<!DOCTYPE html>
<html>
<head>
    <title>MaxIM AI — Executive Personal Assistant Platform</title>
    <meta name="description" content="MaxIM is a high-performance native personal executive assistant with local intelligence, voice, and memory." />
    <meta property="og:title" content="MaxIM AI" />
    <meta property="og:description" content="Executive personal assistant." />
    <meta property="og:image" content="https://example.com/og.png" />
    <link rel="canonical" href="https://example.com" />
    <script type="application/ld+json">{"@context": "https://schema.org", "@type": "SoftwareApplication"}</script>
</head>
<body>
    <h1>MaxIM Intelligent Executive Co-Pilot</h1>
    <h2>System Architecture and Capabilities</h2>
    <img src="logo.png" alt="MaxIM Logo" />
</body>
</html>"""
            return self.audit_html(sample_html, url=clean_url)

        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                res = client.get(clean_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 MaxIM-OpenSEO/1.0"})
                return self.audit_html(res.text, url=clean_url)
        except Exception as e:
            fallback_html = f"<html><head><title>{clean_url}</title></head><body><h1>Target Offline</h1><p>{str(e)}</p></body></html>"
            return self.audit_html(fallback_html, url=clean_url)

    def analyze_keyword_density(self, text: str, target_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates total word count and keyword frequency distribution."""
        words = [w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", text)]
        total_words = len(words)
        freq_map: Dict[str, int] = {}
        for w in words:
            freq_map[w] = freq_map.get(w, 0) + 1

        top_keywords = sorted(
            [{"keyword": k, "count": v, "density_percent": round((v / max(1, total_words)) * 100, 2)}
             for k, v in freq_map.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:15]

        targets_analyzed = []
        if target_keywords:
            for kw in target_keywords:
                kw_clean = kw.lower().strip()
                count = freq_map.get(kw_clean, 0)
                density = round((count / max(1, total_words)) * 100, 2)
                targets_analyzed.append({
                    "keyword": kw,
                    "count": count,
                    "density_percent": density,
                    "status": "optimal (1-3%)" if 1.0 <= density <= 3.0 else ("low (<1%)" if density < 1.0 else "high (>3%)")
                })

        return {
            "total_words": total_words,
            "unique_words": len(freq_map),
            "top_keywords": top_keywords,
            "target_keywords": targets_analyzed
        }

    def list_audits(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM seo_audits ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

# Singleton instance
open_seo = OpenSEOEngine()
