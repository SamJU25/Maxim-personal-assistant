"""
backend/image_generator.py
==========================
Neural Image Generation Engine for MaxIM.
Supports:
1. Pollinations.ai FLUX / SDXL (Zero-API-key, ultra-fast free diffusion)
2. OpenAI DALL-E 3 (if OPENAI_API_KEY is configured)
3. Direct Obsidian vault syncing to vault/02 - Knowledge/Images/
"""

import hashlib
import io
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("maxim.image_generator")

# Ensure backend directory is in path for config
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from config import config
    VAULT_IMAGES_DIR = config.vault_dir / "02 - Knowledge" / "Images"
except Exception:
    VAULT_IMAGES_DIR = Path("F:/MAXIM V2/vault/02 - Knowledge/Images")

VAULT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerationEngine:
    """
    Handles text-to-image synthesis and persists outputs to the Obsidian vault.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or VAULT_IMAGES_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        clean = (prompt or "").strip()
        if not style:
            return clean

        style_lower = style.strip().lower()
        style_modifiers = {
            "photorealistic": "photorealistic, hyper-detailed, 8k resolution, cinematic lighting, sharp focus",
            "anime": "anime aesthetic, vibrant studio ghibli style, detailed linework, digital illustration",
            "cyberpunk": "cyberpunk style, neon glow, futuristic night city lighting, octane render, 8k",
            "cinematic": "cinematic still, 35mm film photograph, dramatic atmospheric lighting, depth of field",
            "digital art": "concept digital art, artstation trending, vibrant color palette, intricate detail",
            "pixel art": "pixel art style, 16-bit retro game aesthetic, clean pixel lines",
            "watercolor": "delicate watercolor painting, soft pigment washes, textured paper",
            "oil painting": "classic oil painting, visible canvas texture and impasto brush strokes"
        }
        mod = style_modifiers.get(style_lower, f"{style} style, high quality")
        return f"{clean}, {mod}"

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = "photorealistic",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes an image from a visual prompt.
        """
        prompt_clean = (prompt or "").strip()
        if not prompt_clean:
            raise ValueError("Visual prompt cannot be empty.")

        enhanced_prompt = self._enhance_prompt(prompt_clean, style)
        clean_seed = seed if seed is not None else int(time.time() * 1000) % 1000000

        # Generate unique local filename
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt_clean.lower())[:32].strip("_")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_hash = hashlib.md5(enhanced_prompt.encode("utf-8")).hexdigest()[:6]
        filename = f"gen_{timestamp_str}_{slug}_{prompt_hash}.jpg"
        target_path = self.output_dir / filename

        image_bytes: Optional[bytes] = None
        provider_used = "pollinations"

        # Attempt 1: Pollinations.ai (Fast, free neural diffusion)
        encoded = urllib.parse.quote(enhanced_prompt)
        direct_web_url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}"

        try:
            req = urllib.request.Request(
                direct_web_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                if resp.status == 200:
                    image_bytes = resp.read()
                    provider_used = "pollinations"
        except Exception as e:
            logger.warning("Pollinations image bytes download failed: %s", e)

        # Attempt 2: OpenAI DALL-E 3 (if API key available)
        if not image_bytes:
            openai_key = os.getenv("OPENAI_API_KEY")
            try:
                from router import model_router
                if not openai_key and "openai" in model_router.providers:
                    openai_key = model_router.providers["openai"].api_key
            except Exception:
                pass

            if openai_key and not openai_key.startswith("mock_"):
                try:
                    import httpx
                    headers = {
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    }
                    dalle_body = {
                        "model": "dall-e-3",
                        "prompt": enhanced_prompt,
                        "n": 1,
                        "size": f"{min(width, 1024)}x{min(height, 1024)}"
                    }
                    with httpx.Client(timeout=30.0) as client:
                        r = client.post("https://api.openai.com/v1/images/generations", json=dalle_body, headers=headers)
                        if r.status_code == 200:
                            img_url = r.json()["data"][0]["url"]
                            img_resp = client.get(img_url)
                            image_bytes = img_resp.content
                            provider_used = "dall-e-3"
                except Exception as e:
                    logger.warning("DALL-E 3 generation failed: %s", e)

        # If bytes were downloaded locally, save to vault
        if image_bytes:
            target_path.write_bytes(image_bytes)
            web_url = f"/api/images/{filename}"
        else:
            # Resilient direct cloud URL fallback so user is never blocked
            web_url = direct_web_url

        # Save Obsidian Companion Note
        note_name = f"{timestamp_str}_{slug}.md"
        note_path = self.output_dir / note_name
        note_content = (
            f"---\n"
            f"title: \"{prompt_clean}\"\n"
            f"date: \"{datetime.now().isoformat()}\"\n"
            f"provider: \"{provider_used}\"\n"
            f"style: \"{style or 'default'}\"\n"
            f"tags: [\"#ai-image\", \"#generation\", \"#{style or 'art'}\"]\n"
            f"---\n\n"
            f"# {prompt_clean}\n\n"
            f"![{prompt_clean}]({web_url})\n\n"
            f"- **Prompt**: {enhanced_prompt}\n"
            f"- **Dimensions**: {width}x{height}\n"
            f"- **Provider**: {provider_used}\n"
        )
        try:
            note_path.write_text(note_content, encoding="utf-8")
        except Exception as e:
            logger.debug("Could not write companion note: %s", e)

        return {
            "status": "success",
            "prompt": prompt_clean,
            "filename": filename,
            "image_url": web_url,
            "direct_url": direct_web_url,
            "local_path": str(target_path.resolve()) if image_bytes else None,
            "markdown": f"![{prompt_clean}]({web_url})",
            "provider": provider_used,
            "width": width,
            "height": height,
        }

    def get_image_path(self, filename: str) -> Optional[Path]:
        """
        Safely retrieves the Path for an image, preventing directory traversal.
        """
        safe_name = Path(filename).name
        candidate = self.output_dir / safe_name
        if candidate.exists() and candidate.is_file():
            return candidate
        return None


# Global singleton instance
image_generator = ImageGenerationEngine()
