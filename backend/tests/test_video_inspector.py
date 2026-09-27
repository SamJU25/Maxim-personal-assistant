"""
Unit and integration tests for Video & Meeting Intelligence Engine (claude-video adaptation).
"""
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from video_inspector import VideoInspectorEngine, format_timestamp, parse_time_str

@pytest.fixture
def temp_env():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_video.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = VideoInspectorEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def sample_video(temp_env):
    engine, tmp_dir, _ = temp_env
    if not engine.ffmpeg_bin:
        pytest.skip("ffmpeg binary not available")
    
    video_path = tmp_dir / "test_sample.mp4"
    cmd = [
        engine.ffmpeg_bin,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=1:size=320x240:rate=10",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=1",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert video_path.exists()
    return video_path

def test_timestamp_utilities():
    assert format_timestamp(45.0) == "00:45"
    assert format_timestamp(125.0) == "02:05"
    assert format_timestamp(3665.0) == "01:01:05"

    assert parse_time_str("00:00:15.500") == 15.5
    assert parse_time_str("01:30") == 90.0
    assert parse_time_str("45.2") == 45.2

def test_inspect_video(temp_env, sample_video):
    engine, _, _ = temp_env
    if not engine.ffprobe_bin:
        pytest.skip("ffprobe not available")
    
    meta = engine.inspect_video(str(sample_video))
    assert meta["inspection_id"] > 0
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["duration_seconds"] > 0.8
    assert "video" in meta["codec_video"].lower() or len(meta["codec_video"]) > 0
    assert meta["size_bytes"] > 0

def test_extract_keyframes(temp_env, sample_video):
    engine, _, vault_dir = temp_env
    frames = engine.extract_keyframes(str(sample_video), interval_seconds=0.5, max_frames=5)
    assert len(frames) >= 1
    for f in frames:
        assert Path(f["frame_path"]).exists()
        assert f["timestamp_str"] is not None

def test_parse_srt(temp_env):
    engine, tmp_dir, _ = temp_env
    srt_file = tmp_dir / "test.srt"
    srt_file.write_text("""1
00:00:01,000 --> 00:00:04,500
Hello team, welcome to the sprint review.

2
00:00:05,000 --> 00:00:09,000
Today we are shipping the new offline video module.
""", encoding="utf-8")

    segments = engine._parse_srt(srt_file)
    assert len(segments) == 2
    assert segments[0]["start"] == 1.0
    assert segments[0]["end"] == 4.5
    assert "sprint review" in segments[0]["text"]
    assert segments[1]["start"] == 5.0
    assert "offline video module" in segments[1]["text"]

def test_parse_vtt(temp_env):
    engine, tmp_dir, _ = temp_env
    vtt_file = tmp_dir / "test.vtt"
    vtt_file.write_text("""WEBVTT

00:01.000 --> 00:05.000
Discussing quarterly roadmap and priorities.
""", encoding="utf-8")

    segments = engine._parse_vtt(vtt_file)
    assert len(segments) == 1
    assert "quarterly roadmap" in segments[0]["text"]

def test_extract_audio_and_transcript_with_srt(temp_env, sample_video):
    engine, _, _ = temp_env
    # Create companion .srt
    srt_file = sample_video.with_suffix(".srt")
    srt_file.write_text("""1
00:00:00,100 --> 00:00:00,900
Quick automated system test demonstration.
""", encoding="utf-8")

    res = engine.extract_audio_and_transcript(str(sample_video))
    assert res["segment_count"] == 1
    assert "Quick automated system" in res["segments"][0]["text"]

def test_synthesize_meeting_summary(temp_env, sample_video):
    engine, _, vault_dir = temp_env
    summary = engine.synthesize_meeting_summary(
        video_path=str(sample_video),
        title="Weekly_Engineering_Sync",
        interval_seconds=0.5
    )
    assert summary["title"] == "Weekly_Engineering_Sync"
    assert Path(summary["vault_path"]).exists()
    
    note_content = Path(summary["vault_path"]).read_text(encoding="utf-8")
    assert "# 🎥 Weekly_Engineering_Sync" in note_content
    assert "Executive Summary" in note_content
    assert "Visual Timeline & Slides" in note_content
    assert "Action Items & Decisions" in note_content

def test_missing_video_raises_error(temp_env):
    engine, _, _ = temp_env
    with pytest.raises(FileNotFoundError):
        engine.inspect_video("non_existent_path.mp4")
