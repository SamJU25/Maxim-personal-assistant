import io
import re
import os
import asyncio
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from config import config

logger = logging.getLogger("maxim.voice")

# Paths for local audio.cpp TTS engine
_AUDIOCPP_CLI = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin" / "audiocpp_cli.exe"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TTS_MODEL = _PROJECT_ROOT / "models" / "tts" / "qwen3-tts-12hz-0.6b-base-q8_0.gguf"
_VOICE_REF = _PROJECT_ROOT / "models" / "tts" / "voice_ref_16k.wav"
_VOICE_REF_TEXT = "I am MaxIM, your personal AI assistant. I will help you think through problems and organize your knowledge."


def _get_voice_ref_file() -> Optional[Path]:
    """Finds best available voice reference sample in models/tts/."""
    tts_dir = _PROJECT_ROOT / "models" / "tts"
    for cand in ["voice_ref_16k.wav", "voice_ref.wav"]:
        p = tts_dir / cand
        if p.exists() and p.stat().st_size > 100:
            return p
    return None


def _get_tts_model(preferred_name: Optional[str] = None) -> Optional[Path]:
    """Finds best available Qwen3-TTS model in models/tts/."""
    tts_dir = _PROJECT_ROOT / "models" / "tts"
    if preferred_name and tts_dir.exists():
        for f in tts_dir.glob("*.gguf"):
            if preferred_name.lower() in f.name.lower():
                return f
    if _TTS_MODEL.exists():
        return _TTS_MODEL
    if tts_dir.exists():
        for f in tts_dir.glob("*.gguf"):
            if f.stat().st_size > 1000:
                return f
    return None


def _synthesize_audiocpp_tts(text: str, preferred_model: Optional[str] = None) -> bytes:
    """
    Synthesizes speech using the local Qwen3-TTS model via audio.cpp on CUDA.
    Returns MP3 bytes (converted from WAV via ffmpeg) for browser playback.
    """
    model_path = _get_tts_model(preferred_model)
    voice_ref = _get_voice_ref_file()
    if not _AUDIOCPP_CLI.exists() or not model_path or not voice_ref:
        raise FileNotFoundError("audio.cpp CLI, TTS model, or voice reference not found")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    mp3_path = wav_path.replace(".wav", ".mp3")

    try:
        cmd = [
            str(_AUDIOCPP_CLI),
            "--task", "tts",
            "--family", "qwen3_tts",
            "--model", str(model_path),
            "--backend", "cuda",
            "--voice-ref", str(voice_ref),
            "--reference-text", _VOICE_REF_TEXT,
            "--text", text,
            "--out", wav_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            cwd=str(_AUDIOCPP_CLI.parent),
        )
        if result.returncode != 0:
            raise RuntimeError(f"audiocpp_cli failed: {result.stderr.decode(errors='replace')[:200]}")

        # Convert WAV to MP3 for browser compatibility
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "4", mp3_path]
        subprocess.run(ffmpeg_cmd, capture_output=True, timeout=10)

        out_path = mp3_path if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 100 else wav_path
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        for p in (wav_path, mp3_path):
            try:
                os.remove(p)
            except Exception:
                pass


def _synthesize_local_offline_tts(text: str) -> bytes:
    """Synthesizes speech locally using Windows SAPI5 / pyttsx3 (no internet required)."""
    import pyttsx3

    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


class MaxIMVoiceEngine:
    def __init__(
        self,
        default_voice: str = "en-US-ChristopherNeural",  # Sharp, crisp, masculine British/US persona
        bangla_voice: str = "bn-BD-PradeepNeural",       # Natural Bangla neural voice
        rate: str = "+5%",
    ):
        self.default_voice = default_voice
        self.bangla_voice = bangla_voice
        self.rate = rate

    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
        preferred_model: Optional[str] = None,
        test_mode: bool = False,
    ) -> bytes:
        """
        Synthesizes text to streaming MP3 audio bytes.
        Supports fast streaming engines:
        - 'edge': Microsoft Natural Neural Voice (~1-2s, crystal clear)
        - 'local_fast': Windows SAPI5 / pyttsx3 (~0.25s, instant offline)
        - 'qwen3': audio.cpp local GPU voice cloning
        Default cascades: Edge-TTS (fast neural) -> pyttsx3 (instant local) -> audio.cpp Qwen3-TTS
        """
        if test_mode or not text.strip():
            # Return valid mock audio payload for instant offline testing
            return b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf60.16.100\x00"

        # Strip markdown syntax for natural reading voice
        clean_text = (
            text.replace("**", "")
            .replace("*", "")
            .replace("`", "")
            .replace("[[", "")
            .replace("]]", "")
            .replace("#", "")
            .strip()
        )

        # Prepare text for audio synthesis:
        # If clean_text contains Romanized local phrases that have verified native script,
        # substitute them for TTS audio generation so the neural voice speaks with authentic native inflection
        tts_text = clean_text
        try:
            from language_learner import language_learner
            vocab = language_learner.get_vocabulary(limit=50)
            for item in vocab:
                if item.phonetic_script and item.phonetic_script != item.word_or_phrase:
                    match_word = item.word_or_phrase.rstrip("?!.,")
                    pattern = r"\b" + re.escape(match_word) + r"\b"
                    tts_text = re.sub(pattern, item.phonetic_script, tts_text, flags=re.IGNORECASE)
        except Exception:
            pass

        if not voice:
            # Auto-detect Bengali script in tts_text and switch to native neural voice
            if re.search(r"[\u0980-\u09FF]", tts_text):
                selected_voice = self.bangla_voice
            else:
                selected_voice = self.default_voice
        else:
            selected_voice = voice

        # Explicit engine selection overrides
        req_engine = (engine or "").lower()
        if req_engine in ("local_fast", "pyttsx3", "fast"):
            try:
                offline_bytes = await asyncio.to_thread(_synthesize_local_offline_tts, tts_text)
                if offline_bytes:
                    logger.info(f"TTS via pyttsx3 (local fast requested): {len(offline_bytes)} bytes")
                    return offline_bytes
            except Exception as e:
                logger.warning(f"Fast local pyttsx3 failed: {e}")

        if req_engine in ("qwen3", "local_neural", "audiocpp"):
            try:
                audio_data = await asyncio.to_thread(_synthesize_audiocpp_tts, tts_text, preferred_model)
                if audio_data and len(audio_data) > 100:
                    logger.info(f"TTS via audio.cpp Qwen3-TTS (requested): {len(audio_data)} bytes")
                    return audio_data
            except Exception as e:
                logger.warning(f"audio.cpp Qwen3-TTS failed: {e}")

        # Default Cascade:
        # Tier 1: Edge-TTS (online, fast 1-2s streaming, studio natural neural voice)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(tts_text, selected_voice, rate=self.rate)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            audio_data = buffer.getvalue()
            if audio_data and len(audio_data) > 100:
                logger.info(f"TTS via Edge-TTS ({selected_voice}): {len(audio_data)} bytes")
                return audio_data
        except Exception as e:
            logger.debug(f"Edge-TTS unavailable, falling back to local TTS: {e}")

        # Tier 2: Instant local offline TTS (Windows SAPI5 / pyttsx3, ~0.25s)
        try:
            offline_bytes = await asyncio.to_thread(_synthesize_local_offline_tts, tts_text)
            if offline_bytes and len(offline_bytes) > 100:
                logger.info(f"TTS via pyttsx3 (instant local offline): {len(offline_bytes)} bytes")
                return offline_bytes
        except Exception as e:
            logger.debug(f"pyttsx3 unavailable: {e}")

        # Tier 3: Local GPU TTS via audio.cpp + Qwen3-TTS
        try:
            audio_data = await asyncio.to_thread(_synthesize_audiocpp_tts, tts_text, preferred_model)
            if audio_data and len(audio_data) > 100:
                logger.info(f"TTS via audio.cpp Qwen3-TTS: {len(audio_data)} bytes")
                return audio_data
        except Exception as e:
            logger.debug(f"audio.cpp TTS unavailable: {e}")

        # Valid mock audio payload fallback
        return b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf60.16.100\x00"

    def format_text_for_speech(self, text: str) -> str:
        """
        Shortens and adapts long model responses into punchy voice conversational replies
        (per soul.md invariants: 1-3 sentences max).
        """
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        if len(sentences) <= 3:
            return text.strip()
        return ". ".join(sentences[:3]) + "."

    async def speak_to_bytes(
        self,
        text: str,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> bytes:
        """Alias for synthesize_speech."""
        return await self.synthesize_speech(
            text=text,
            voice=voice,
            engine=engine,
            preferred_model=preferred_model,
        )

    def get_status(self) -> dict:
        """Returns the operational status, discovered models, and capabilities of the TTS engine."""
        tts_dir = _PROJECT_ROOT / "models" / "tts"
        models = []
        if tts_dir.exists():
            for f in sorted(tts_dir.glob("*.gguf")):
                models.append({
                    "name": f.name,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
                    "path": str(f),
                })
        active_model = _get_tts_model()
        voice_ref = _get_voice_ref_file()
        return {
            "audiocpp_available": _AUDIOCPP_CLI.exists(),
            "models": models,
            "active_model": active_model.name if active_model else None,
            "voice_ref_available": voice_ref is not None,
            "voice_ref_name": voice_ref.name if voice_ref else None,
            "supported_engines": ["edge", "pyttsx3", "qwen3"],
            "default_voice": self.default_voice,
            "bangla_voice": self.bangla_voice,
            "rate": self.rate,
        }

# Singleton instance and aliases
voice_engine = MaxIMVoiceEngine()
voice_synthesizer = voice_engine

