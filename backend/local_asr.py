"""
MaxIM Local Speech-to-Text (ASR) Engine.
Tier 1: High-performance Qwen3-ASR via audio.cpp on CUDA (100% offline, GPU-accelerated).
Tier 2: Faster-Whisper with CTranslate2 and CUDA/CPU acceleration with Silero VAD.
"""
import io
import os
import sys
import tempfile
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("maxim.local_asr")

_AUDIOCPP_CLI = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin" / "audiocpp_cli.exe"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ASR_DIR = _PROJECT_ROOT / "models" / "asr"


def normalize_asr_transcript(text: str) -> str:
    """Corrects common acoustic and phonetic speech recognition errors for MaxIM domain vocabulary."""
    if not text:
        return ""
    import re
    # Fix MaxIM name misrecognitions
    text = re.sub(r"\b(magazine|maximum|max in|max aim|mexican|macsim|maxine|magsim|max im|max it|make scene|mack sim|maksim)\b", "MaxIM", text, flags=re.I)
    # Fix system vocabulary
    text = re.sub(r"\b(tell us|tel us|tell os|tel os)\b", "TELOS", text, flags=re.I)
    text = re.sub(r"\b(life os|life of|life us)\b", "LifeOS", text, flags=re.I)
    text = re.sub(r"\b(bitter bot|peter bot|better bot)\b", "Bitterbot", text, flags=re.I)
    text = re.sub(r"\b(open human)\b", "OpenHuman", text, flags=re.I)
    text = re.sub(r"\b(zylos|zilos|xylos)\b", "Zylos", text, flags=re.I)
    text = re.sub(r"\b(hermes|her mess)\b", "Hermes", text, flags=re.I)
    return text.strip()


def _get_audiocpp_asr_model(preferred_name: Optional[str] = None) -> Optional[Path]:
    """Finds the best available Qwen3-ASR GGUF model in models/asr/."""
    if preferred_name:
        for f in _ASR_DIR.glob("*.gguf"):
            if preferred_name.lower() in f.name.lower():
                return f

    candidates = [
        _ASR_DIR / "qwen3-asr-0.6b-q8_0.gguf",
        _ASR_DIR / "qwen3-asr-1.7b-q8_0.gguf",
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 1000:
            return c
    # Fallback to any .gguf in models/asr
    if _ASR_DIR.exists():
        for f in _ASR_DIR.glob("*.gguf"):
            if f.stat().st_size > 1000:
                return f
    return None


def _transcribe_audiocpp(audio_path: Path, preferred_model: Optional[str] = None) -> Optional[str]:
    """
    Transcribes audio using local Qwen3-ASR via audio.cpp on CUDA.
    Converts input audio to 16kHz mono PCM WAV via ffmpeg first.
    """
    if not _AUDIOCPP_CLI.exists():
        return None

    model_path = _get_audiocpp_asr_model(preferred_model)
    if not model_path:
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_16k_path = tmp_wav.name

    try:
        # Convert any input audio (WebM, MP3, WAV, etc.) to 16kHz mono WAV
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            wav_16k_path,
        ]
        ff_res = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=10)
        if ff_res.returncode != 0 or not os.path.exists(wav_16k_path) or os.path.getsize(wav_16k_path) < 100:
            return None

        cmd = [
            str(_AUDIOCPP_CLI),
            "--task", "asr",
            "--family", "qwen3_asr",
            "--model", str(model_path),
            "--backend", "cuda",
            "--audio", wav_16k_path,
            "--metrics",
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_AUDIOCPP_CLI.parent),
        )

        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.startswith("text_output="):
                    text = line[len("text_output="):].strip()
                    if text:
                        text = normalize_asr_transcript(text)
                        logger.info(f"ASR via audio.cpp Qwen3-ASR ({model_path.name}): {text}")
                        return text
        else:
            logger.warning(f"audio.cpp ASR error ({res.returncode}): {res.stderr[:200]}")
        return None
    except Exception as e:
        logger.warning(f"audio.cpp ASR invocation failed: {e}")
        return None
    finally:
        if os.path.exists(wav_16k_path):
            try:
                os.remove(wav_16k_path)
            except Exception:
                pass


class LocalASREngine:
    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self._model = None
        self._device = "cuda" if self._is_cuda_available() else "cpu"

    def _is_cuda_available(self) -> bool:
        try:
            import ctranslate2
            return "cuda" in ctranslate2.get_supported_compute_types("cuda")
        except Exception:
            return False

    def get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                compute = "float16" if self._device == "cuda" else "int8"
                logger.info(f"Loading local ASR model ({self.model_size}) on {self._device} ({compute})...")
                self._model = WhisperModel(
                    self.model_size,
                    device=self._device,
                    compute_type=compute,
                    download_root=os.path.expanduser("~/.cache/huggingface/hub"),
                )
                logger.info("Local ASR model ready.")
            except Exception as e:
                logger.warning(f"Could not load faster-whisper on {self._device}, trying cpu: {e}")
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                )
        return self._model

    def transcribe_file(self, audio_path: str | Path, language: Optional[str] = "en", preferred_model: Optional[str] = None) -> str:
        """
        Transcribes an audio file on disk to text.
        Tier 1: audio.cpp Qwen3-ASR on CUDA (fastest, high accuracy).
        Tier 2: Faster-Whisper on CUDA/CPU.
        """
        path_obj = Path(audio_path)
        if not path_obj.exists():
            return ""

        # Tier 1: Try audio.cpp Qwen3-ASR on CUDA
        try:
            audiocpp_text = _transcribe_audiocpp(path_obj, preferred_model=preferred_model)
            if audiocpp_text:
                return audiocpp_text
        except Exception as e:
            logger.warning(f"audio.cpp ASR attempt failed, falling back to Faster-Whisper: {e}")

        # Tier 2: Faster-Whisper
        model = self.get_model()
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=2,
            initial_prompt="MaxIM, LifeOS, TELOS, Sam, Bitterbot, Hermes, AI assistant",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        texts = [s.text.strip() for s in segments if s.text and s.text.strip()]
        result = normalize_asr_transcript(" ".join(texts).strip())
        logger.info(f"ASR via Faster-Whisper ({self.model_size}): {result}")
        return result

    def transcribe_bytes(self, audio_bytes: bytes, suffix: str = ".webm", language: Optional[str] = "en", preferred_model: Optional[str] = None) -> str:
        """Transcribes raw audio bytes (WebM, WAV, MP3) to text."""
        if not audio_bytes:
            return ""

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path, language=language, preferred_model=preferred_model)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def get_status(self) -> dict:
        """Returns the operational status, discovered models, and hardware capabilities of the ASR engine."""
        models = []
        if _ASR_DIR.exists():
            for f in sorted(_ASR_DIR.glob("*.gguf")):
                models.append({
                    "name": f.name,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
                    "path": str(f),
                })
        active_model = _get_audiocpp_asr_model()
        return {
            "audiocpp_available": _AUDIOCPP_CLI.exists(),
            "cuda_available": self._is_cuda_available(),
            "models": models,
            "active_model": active_model.name if active_model else None,
            "whisper_fallback_device": self._device,
            "whisper_model_size": self.model_size,
        }

local_asr = LocalASREngine()

