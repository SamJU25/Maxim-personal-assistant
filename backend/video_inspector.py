"""
Video & Meeting Intelligence Engine for MaxIM (Adapted from bradautomates/claude-video).
Extracts video metadata via FFprobe, visual keyframes via FFmpeg, audio/subtitles,
and synthesizes structured meeting dossiers with action items directly to Obsidian.
Repository reference: https://github.com/bradautomates/claude-video
"""
import subprocess
import shutil
import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config import config

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def parse_time_str(time_str: str) -> float:
    parts = time_str.replace(",", ".").split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return float(parts[0])

def find_binary(name: str) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    # Common Windows WinGet / Chocolatey paths
    winget_base = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for candidate in winget_base.glob(f"**/{name}.exe"):
        if candidate.is_file():
            return str(candidate)
    return None

class VideoInspectorEngine:
    def __init__(self, db_path: Optional[Path] = None, vault_dir: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.vault_dir = vault_dir or config.vault_dir
        self.ffmpeg_bin = find_binary("ffmpeg")
        self.ffprobe_bin = find_binary("ffprobe")
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
            CREATE TABLE IF NOT EXISTS video_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_path TEXT NOT NULL,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                fps REAL,
                codec_video TEXT,
                codec_audio TEXT,
                size_bytes INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS video_frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                timestamp_seconds REAL NOT NULL,
                timestamp_str TEXT NOT NULL,
                frame_path TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (inspection_id) REFERENCES video_inspections(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS video_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                start_seconds REAL NOT NULL,
                end_seconds REAL NOT NULL,
                text TEXT NOT NULL,
                speaker TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (inspection_id) REFERENCES video_inspections(id) ON DELETE CASCADE
            );
            """)

    def inspect_video(self, video_path: str) -> Dict[str, Any]:
        """Runs ffprobe on the target video and returns stream metadata."""
        v_path = Path(video_path).resolve()
        if not v_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not self.ffprobe_bin:
            raise RuntimeError("ffprobe binary not found on the system.")

        cmd = [
            self.ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(v_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {res.stderr}")

        data = json.loads(res.stdout)
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        duration = float(format_info.get("duration", 0.0))
        size_bytes = int(format_info.get("size", v_path.stat().st_size))

        v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        codec_video = v_stream.get("codec_name", "unknown")
        codec_audio = a_stream.get("codec_name", "none")

        fps = 0.0
        fps_str = v_stream.get("r_frame_rate", "0/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            if float(den) > 0:
                fps = round(float(num) / float(den), 2)

        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO video_inspections (video_path, duration_seconds, width, height, fps, codec_video, codec_audio, size_bytes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(v_path), duration, width, height, fps, codec_video, codec_audio, size_bytes, now))
            inspection_id = cursor.lastrowid
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "video_path": str(v_path),
            "duration_seconds": duration,
            "duration_str": format_timestamp(duration),
            "width": width,
            "height": height,
            "fps": fps,
            "codec_video": codec_video,
            "codec_audio": codec_audio,
            "size_bytes": size_bytes,
            "created_at": now
        }

    def extract_keyframes(
        self,
        video_path: str,
        interval_seconds: float = 10.0,
        max_frames: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Samples visual frames at regular timestamp intervals and stores them in the vault cache.
        """
        v_path = Path(video_path).resolve()
        if not v_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not self.ffmpeg_bin:
            raise RuntimeError("ffmpeg binary not found on the system.")

        # Ensure inspection record exists
        inspection = self.inspect_video(str(v_path))
        inspection_id = inspection["inspection_id"]
        duration = inspection["duration_seconds"]

        # Output frames directory inside vault
        safe_name = "".join(c for c in v_path.stem if c.isalnum() or c in ("-", "_")).strip() or "video"
        frames_dir = self.vault_dir / "02 - Knowledge" / "Video Intel" / "frames" / safe_name
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Clear any existing frames in output directory
        for existing in frames_dir.glob("frame_*.jpg"):
            try:
                existing.unlink()
            except Exception:
                pass

        # Calculate fps filter: fps = 1 / interval
        rate_val = 1.0 / max(0.5, interval_seconds)
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(v_path),
            "-vf", f"fps={rate_val:.4f}",
            "-q:v", "2",
            "-vframes", str(max_frames),
            str(frames_dir / "frame_%04d.jpg")
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"ffmpeg frame extraction failed: {res.stderr}")

        # Scan extracted frames and register into DB
        frame_files = sorted(frames_dir.glob("frame_*.jpg"))
        registered_frames = []
        now = utc_now_iso()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for idx, f_path in enumerate(frame_files):
                # Approximate timestamp: index * interval_seconds, capped at duration
                approx_time = min(duration, idx * interval_seconds)
                time_str = format_timestamp(approx_time)
                cursor.execute("""
                INSERT INTO video_frames (inspection_id, timestamp_seconds, timestamp_str, frame_path, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (inspection_id, approx_time, time_str, str(f_path), f"Keyframe at {time_str}", now))
                registered_frames.append({
                    "id": cursor.lastrowid,
                    "inspection_id": inspection_id,
                    "timestamp_seconds": approx_time,
                    "timestamp_str": time_str,
                    "frame_path": str(f_path),
                    "filename": f_path.name
                })
            conn.commit()

        return registered_frames

    def extract_audio_and_transcript(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts subtitles if available (external .srt/.vtt or embedded stream),
        or detects dialogue / speech windows using audio silence detection.
        """
        v_path = Path(video_path).resolve()
        if not v_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        inspection = self.inspect_video(str(v_path))
        inspection_id = inspection["inspection_id"]

        segments = []

        # 1. Check external subtitle file (.srt or .vtt alongside video)
        srt_candidate = v_path.with_suffix(".srt")
        vtt_candidate = v_path.with_suffix(".vtt")

        if srt_candidate.exists():
            segments = self._parse_srt(srt_candidate)
        elif vtt_candidate.exists():
            segments = self._parse_vtt(vtt_candidate)
        elif self.ffmpeg_bin:
            # 2. Try extracting embedded subtitle stream
            safe_name = "".join(c for c in v_path.stem if c.isalnum() or c in ("-", "_")).strip()
            temp_srt = self.vault_dir / "02 - Knowledge" / "Video Intel" / "frames" / safe_name / "subtitles.srt"
            temp_srt.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                self.ffmpeg_bin,
                "-y",
                "-i", str(v_path),
                "-map", "0:s:0",
                str(temp_srt)
            ]
            sub_res = subprocess.run(cmd, capture_output=True, text=True)
            if sub_res.returncode == 0 and temp_srt.exists() and temp_srt.stat().st_size > 0:
                segments = self._parse_srt(temp_srt)
            else:
                # 3. Detect speech activity windows using silence detection
                cmd_silence = [
                    self.ffmpeg_bin,
                    "-i", str(v_path),
                    "-af", "silencedetect=noise=-30dB:d=0.5",
                    "-f", "null",
                    "-"
                ]
                sil_res = subprocess.run(cmd_silence, capture_output=True, text=True)
                segments = self._parse_silence_segments(sil_res.stderr, inspection["duration_seconds"])

        # Store segments in DB
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for s in segments:
                cursor.execute("""
                INSERT INTO video_transcripts (inspection_id, start_seconds, end_seconds, text, speaker, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (inspection_id, s["start"], s["end"], s["text"], s.get("speaker", "Speaker"), now))
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "video_path": str(v_path),
            "segment_count": len(segments),
            "segments": segments
        }

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        segments = []
        content = srt_path.read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(r"(\d+)\r?\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\r?\n([\s\S]*?)(?=\r?\n\r?\n|\Z)")
        for match in pattern.finditer(content):
            _, start_str, end_str, text = match.groups()
            clean_text = " ".join(text.strip().splitlines())
            start_sec = parse_time_str(start_str)
            end_sec = parse_time_str(end_str)
            segments.append({
                "start": round(start_sec, 2),
                "end": round(end_sec, 2),
                "start_str": format_timestamp(start_sec),
                "end_str": format_timestamp(end_sec),
                "text": clean_text
            })
        return segments

    def _parse_vtt(self, vtt_path: Path) -> List[Dict[str, Any]]:
        segments = []
        content = vtt_path.read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(r"(\d{2}:)?\d{2}:\d{2}\.\d{3}\s*-->\s*(\d{2}:)?\d{2}:\d{2}\.\d{3}")
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "-->" in line:
                parts = line.split("-->")
                start_sec = parse_time_str(parts[0].strip())
                end_sec = parse_time_str(parts[1].strip().split()[0])
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                segments.append({
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "start_str": format_timestamp(start_sec),
                    "end_str": format_timestamp(end_sec),
                    "text": " ".join(text_lines)
                })
            i += 1
        return segments

    def _parse_silence_segments(self, ffmpeg_log: str, total_duration: float) -> List[Dict[str, Any]]:
        """Extracts speech intervals between detected silence intervals."""
        silence_starts = [float(m.group(1)) for m in re.finditer(r"silence_start: ([\d\.]+)", ffmpeg_log)]
        silence_ends = [float(m.group(1)) for m in re.finditer(r"silence_end: ([\d\.]+)", ffmpeg_log)]
        
        segments = []
        current_pos = 0.0
        for s_start, s_end in zip(silence_starts, silence_ends):
            if s_start > current_pos + 1.0:
                segments.append({
                    "start": round(current_pos, 2),
                    "end": round(s_start, 2),
                    "start_str": format_timestamp(current_pos),
                    "end_str": format_timestamp(s_start),
                    "text": f"[Speech Activity from {format_timestamp(current_pos)} to {format_timestamp(s_start)}]"
                })
            current_pos = s_end

        if current_pos < total_duration - 1.0:
            segments.append({
                "start": round(current_pos, 2),
                "end": round(total_duration, 2),
                "start_str": format_timestamp(current_pos),
                "end_str": format_timestamp(total_duration),
                "text": f"[Speech Activity from {format_timestamp(current_pos)} to {format_timestamp(total_duration)}]"
            })

        if not segments and total_duration > 0:
            segments.append({
                "start": 0.0,
                "end": total_duration,
                "start_str": "00:00",
                "end_str": format_timestamp(total_duration),
                "text": f"[Full Speech/Audio Track: {format_timestamp(total_duration)}]"
            })
        return segments

    def synthesize_meeting_summary(
        self,
        video_path: str,
        title: Optional[str] = None,
        interval_seconds: float = 15.0
    ) -> Dict[str, Any]:
        """
        Compiles visual keyframes, audio segments, and generates a structured meeting dossier
        with action items saved directly into Obsidian vault.
        """
        v_path = Path(video_path).resolve()
        doc_title = title or f"Meeting_{v_path.stem}"
        clean_title = "".join(c for c in doc_title if c.isalnum() or c in (" ", "_", "-")).strip()

        # 1. Metadata inspection
        meta = self.inspect_video(str(v_path))
        # 2. Extract keyframes
        frames = self.extract_keyframes(str(v_path), interval_seconds=interval_seconds, max_frames=20)
        # 3. Extract audio & transcript
        trans = self.extract_audio_and_transcript(str(v_path))

        # 4. Generate Obsidian Markdown Note
        now = utc_now_iso()
        md = f"# 🎥 {clean_title}\n\n"
        md += f"> **File:** `{v_path.name}`\n"
        md += f"> **Duration:** `{meta['duration_str']}` | **Resolution:** `{meta['width']}x{meta['height']}` | **FPS:** `{meta['fps']}`\n"
        md += f"> **Codecs:** Video: `{meta['codec_video']}`, Audio: `{meta['codec_audio']}`\n"
        md += f"> **Generated:** `{now}`\n"
        md += f"> **Tags:** #video-intel #meeting-notes #executive-brief\n\n"

        md += "## 📌 Executive Summary\n"
        md += f"Comprehensive video inspection and analysis for `{v_path.name}`. "
        md += f"Processed {len(frames)} visual keyframes across {meta['duration_str']} of recorded material.\n\n"

        md += "## 🖼️ Visual Timeline & Slides\n"
        if frames:
            for f in frames:
                f_obj = Path(f["frame_path"])
                # Obsidian relative wikilink to frame
                md += f"- **[{f['timestamp_str']}]**: ![[frames/{f_obj.parent.name}/{f_obj.name}]]\n"
        else:
            md += "*No visual frames sampled.*\n"
        md += "\n"

        md += "## 💬 Key Discussion Points & Dialogue\n"
        if trans["segments"]:
            for seg in trans["segments"][:25]:
                md += f"- **`[{seg['start_str']} - {seg['end_str']}]`**: {seg['text']}\n"
        else:
            md += "*No transcribed dialogue segments found.*\n"
        md += "\n"

        md += "## ✅ Action Items & Decisions\n"
        md += f"- [ ] Review visual slides from `{v_path.name}` at key transition points.\n"
        md += f"- [ ] Verify recorded technical decisions against active LifeOS projects.\n"
        md += f"- [ ] Archive raw recording once key deliverables are extracted.\n\n"

        md += "---\n*Generated by MaxIM Video Intelligence Engine*\n"

        # Write to vault/02 - Knowledge/Video Intel/<clean_title>.md
        out_dir = self.vault_dir / "02 - Knowledge" / "Video Intel"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{clean_title}.md"
        out_file.write_text(md, encoding="utf-8")

        return {
            "title": clean_title,
            "vault_path": str(out_file),
            "duration": meta["duration_str"],
            "frames_extracted": len(frames),
            "transcript_segments": len(trans["segments"]),
            "summary_preview": md[:400]
        }

# Singleton instance
video_inspector = VideoInspectorEngine()
