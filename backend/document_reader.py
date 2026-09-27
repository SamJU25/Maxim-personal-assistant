"""
Document & Image Reader Engine for MaxIM.
Extracts clean, token-budgeted text from documents (PDF, DOCX, TXT, CSV, JSON, Code)
and visual intelligence / metadata from images (PNG, JPG, WEBP, GIF, BMP).
"""
import io
import os
import re
import json
import base64
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from config import config

logger = logging.getLogger("maxim.document_reader")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DocumentReaderEngine:
    def __init__(self, vault_dir: Optional[Path] = None):
        self.vault_dir = vault_dir or config.vault_dir
        self.attachments_dir = self.vault_dir / "01 - Memory" / "Attachments"
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, file_path_str: str) -> Optional[Path]:
        """Resolves file path from absolute path, vault relative path, or attachments folder."""
        if not file_path_str or not file_path_str.strip():
            return None
        clean_str = file_path_str.strip().strip('"').strip("'")
        p = Path(clean_str)

        # 1. Direct absolute path
        if p.is_absolute() and p.exists() and p.is_file():
            return p

        # 2. Inside vault directory
        vault_cand = (self.vault_dir / clean_str).resolve()
        if vault_cand.exists() and vault_cand.is_file():
            return vault_cand

        # 3. Inside attachments directory
        att_cand = (self.attachments_dir / p.name).resolve()
        if att_cand.exists() and att_cand.is_file():
            return att_cand

        # 4. Search in vault recursively by filename
        for cand in self.vault_dir.rglob(p.name):
            if cand.is_file():
                return cand

        # 5. Check in current project root
        proj_root = Path(__file__).resolve().parent.parent
        proj_cand = (proj_root / clean_str).resolve()
        if proj_cand.exists() and proj_cand.is_file():
            return proj_cand

        return None

    def save_attachment_bytes(self, filename: str, data_bytes: bytes) -> Path:
        """Saves uploaded attachment bytes to vault/01 - Memory/Attachments/."""
        safe_name = re.sub(r"[^\w\-_\.]", "_", filename)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = self.attachments_dir / f"{ts}_{safe_name}"
        target_path.write_bytes(data_bytes)
        return target_path

    def save_attachment_base64(self, filename: str, data_url_or_b64: str) -> Path:
        """Decodes base64 / data URL and saves to attachments directory."""
        b64_str = data_url_or_b64
        if "," in data_url_or_b64:
            b64_str = data_url_or_b64.split(",", 1)[1]
        decoded = base64.b64decode(b64_str)
        return self.save_attachment_bytes(filename, decoded)

    def read_document(self, file_path_str: str, max_chars: int = 15000) -> Dict[str, Any]:
        """
        Reads any document or code file:
        - PDF (.pdf) via pypdf
        - Word (.docx) via stdlib zipfile XML parsing
        - Tabular CSV (.csv) formatted as markdown
        - Code & Text (.txt, .md, .py, .json, .log, .yaml, etc.)
        """
        path = self.resolve_path(file_path_str)
        if not path or not path.exists():
            return {
                "success": False,
                "error": f"File not found: '{file_path_str}'. Please verify the file path exists.",
                "file_path": file_path_str,
            }

        suffix = path.suffix.lower()
        size_bytes = path.stat().st_size
        text_content = ""
        metadata: Dict[str, Any] = {
            "file_name": path.name,
            "file_path": str(path.resolve()),
            "extension": suffix,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
        }

        try:
            if suffix == ".pdf":
                text_content, pdf_meta = self._extract_pdf(path)
                metadata.update(pdf_meta)
            elif suffix == ".docx":
                text_content, docx_meta = self._extract_docx(path)
                metadata.update(docx_meta)
            elif suffix == ".csv":
                text_content, csv_meta = self._extract_csv(path)
                metadata.update(csv_meta)
            elif suffix == ".json":
                text_content = self._extract_json(path)
            else:
                # Standard text / code files
                text_content = self._extract_text(path)

            truncated = False
            total_chars = len(text_content)
            if total_chars > max_chars:
                text_content = text_content[:max_chars] + f"\n\n... [Content truncated at {max_chars} of {total_chars} characters] ..."
                truncated = True

            return {
                "success": True,
                "metadata": metadata,
                "content": text_content,
                "total_chars": total_chars,
                "truncated": truncated,
                "timestamp": utc_now_iso(),
            }
        except Exception as e:
            logger.error(f"Error reading document {path}: {e}")
            return {
                "success": False,
                "error": f"Failed to extract document contents: {str(e)}",
                "file_path": str(path),
            }

    def _extract_pdf(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """Extracts text from PDF using pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            num_pages = len(reader.pages)
            extracted_pages: List[str] = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(f"--- Page {i + 1} ---\n{page_text.strip()}")
            full_text = "\n\n".join(extracted_pages)
            return full_text, {"page_count": num_pages, "parser": "pypdf"}
        except ImportError:
            return f"[PDF file: {path.name}, size: {path.stat().st_size} bytes - pypdf required for text parsing]", {"page_count": 0}

    def _extract_docx(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """Extracts text from Word .docx file using stdlib zipfile and XML parsing."""
        with zipfile.ZipFile(path) as docx_zip:
            xml_content = docx_zip.read("word/document.xml")
        
        tree = ET.fromstring(xml_content)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: List[str] = []

        for p_elem in tree.iterfind(".//w:p", ns):
            texts = [t.text for t in p_elem.iterfind(".//w:t", ns) if t.text]
            p_text = "".join(texts).strip()
            if p_text:
                paragraphs.append(p_text)

        full_text = "\n\n".join(paragraphs)
        return full_text, {"paragraph_count": len(paragraphs), "parser": "docx_xml"}

    def _extract_csv(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """Extracts and formats CSV as a readable markdown table."""
        import csv
        raw = path.read_text(encoding="utf-8", errors="replace")
        reader = csv.reader(io.StringIO(raw))
        rows = list(reader)
        if not rows:
            return "(Empty CSV file)", {"row_count": 0}

        headers = rows[0]
        data_rows = rows[1:100]
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        body_lines = ["| " + " | ".join(row) + " |" for row in data_rows]

        md_table = "\n".join([header_line, sep_line] + body_lines)
        if len(rows) > 101:
            md_table += f"\n\n*(Showing 100 of {len(rows) - 1} data rows)*"

        return md_table, {"total_rows": len(rows), "columns": len(headers)}

    def _extract_json(self, path: Path) -> str:
        """Extracts and pretty-prints JSON file."""
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            return raw

    def _extract_text(self, path: Path) -> str:
        """Reads text file with UTF-8 encoding and defensive fallback."""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="latin-1")
            except Exception:
                return path.read_text(encoding="utf-8", errors="replace")

    async def inspect_image(
        self,
        image_path_str: str,
        prompt: Optional[str] = None,
        auto_boot_local: bool = False,
    ) -> Dict[str, Any]:
        """
        Inspects an image:
        1. Reads dimensions, format, color space, size using PIL.
        2. Queries local neural vision model (Qwen3VL via native llama-server with mmproj) if available.
        3. If unavailable or disabled, queries connected cloud multimodal provider (GPT-4o, Claude 3.5, Gemini).
        4. Falls back to verified local structural dossier.
        """
        path = self.resolve_path(image_path_str)
        if not path or not path.exists():
            return {
                "success": False,
                "error": f"Image file not found: '{image_path_str}'.",
                "image_path": image_path_str,
            }

        try:
            from PIL import Image
            with Image.open(path) as img:
                width, height = img.size
                img_format = img.format or "UNKNOWN"
                mode = img.mode

            size_bytes = path.stat().st_size
            aspect_ratio = round(width / max(height, 1), 2)

            raw_bytes = path.read_bytes()
            b64_data = base64.b64encode(raw_bytes).decode("utf-8")
            mime_type = f"image/{img_format.lower()}" if img_format.lower() in ("png", "jpeg", "webp", "gif") else "image/jpeg"

            visual_description = None
            vision_engine = "local_structural"

            # 1. Attempt Local Multimodal Vision (Qwen3VL via native llama-server with mmproj)
            try:
                from local_model_manager import local_model_manager
                # Check if server is running or if auto-boot is requested
                server_ready = local_model_manager.is_server_ready(local_model_manager._active_port)
                if not server_ready and auto_boot_local:
                    local_vision = local_model_manager.select_best_model(task_type="vision")
                    if local_vision:
                        try:
                            local_model_manager.ensure_model_running(local_vision["path"])
                            server_ready = local_model_manager.is_server_ready(local_model_manager._active_port)
                        except Exception as boot_err:
                            logger.debug(f"Could not auto-boot local vision model: {boot_err}")

                if server_ready:
                    r_info = local_model_manager.get_running_model_info(local_model_manager._active_port)
                    running_id = r_info.get("id", "") if r_info else ""
                    # Check if running model is a vision model
                    is_vision = any(k in running_id.lower() for k in ("vl", "vision", "qwen3vl", "image"))
                    if not is_vision and auto_boot_local:
                        local_vision = local_model_manager.select_best_model(task_type="vision")
                        if local_vision:
                            try:
                                local_model_manager.ensure_model_running(local_vision["path"])
                                is_vision = True
                                r_info = local_model_manager.get_running_model_info(local_model_manager._active_port)
                                running_id = r_info.get("id", "") if r_info else local_vision["file_name"]
                            except Exception as boot_err:
                                logger.debug(f"Could not hot-swap to local vision model: {boot_err}")

                    if is_vision:
                        user_q = prompt or "Describe this image in detail, including all visible objects, text, layout, colors, and key details."
                        import httpx
                        payload = {
                            "model": Path(running_id).name if running_id else "qwen3vl",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": user_q},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{mime_type};base64,{b64_data}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            "max_tokens": 600,
                            "temperature": 0.2,
                        }
                        async with httpx.AsyncClient(timeout=45.0) as client:
                            resp = await client.post(
                                f"http://127.0.0.1:{local_model_manager._active_port}/v1/chat/completions",
                                json=payload
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                choices = data.get("choices", [])
                                if choices and choices[0].get("message", {}).get("content"):
                                    visual_description = choices[0]["message"]["content"].strip()
                                    model_label = Path(running_id).name if running_id else "Qwen3VL-4B"
                                    vision_engine = f"local_neural_vision ({model_label})"
            except Exception as e:
                logger.debug(f"Local vision inspection query failed: {e}")

            # 2. Check if connected cloud provider with vision capability is available
            if not visual_description:
                try:
                    from router import model_router
                    cloud_provs = model_router.get_connected_cloud_providers()
                    if cloud_provs:
                        chosen_p = cloud_provs[0]
                        client, _ = model_router.get_async_client(chosen_p["provider"])
                        user_q = prompt or "Describe this image in detail, including all visible objects, text, layout, colors, and key details."
                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_q},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{b64_data}"
                                        }
                                    }
                                ]
                            }
                        ]
                        comp = await client.chat.completions.create(
                            model=chosen_p["model_name"],
                            messages=messages,
                            max_tokens=600,
                        )
                        visual_description = comp.choices[0].message.content
                        vision_engine = f"cloud_multimodal ({chosen_p['name']})"
                except Exception as e:
                    logger.debug(f"Cloud multimodal query failed or not configured: {e}")

            # 3. Fallback to structural description
            if not visual_description:
                visual_description = (
                    f"Image '{path.name}' ({width}x{height} px, {img_format} format, {mode} color mode, {round(size_bytes / 1024, 1)} KB). "
                    f"Aspect ratio is {aspect_ratio}:1. Local structural properties verified successfully."
                )

            return {
                "success": True,
                "file_name": path.name,
                "file_path": str(path.resolve()),
                "dimensions": {"width": width, "height": height},
                "aspect_ratio": aspect_ratio,
                "format": img_format,
                "color_mode": mode,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2),
                "visual_description": visual_description,
                "vision_engine": vision_engine,
                "timestamp": utc_now_iso(),
            }
        except Exception as e:
            logger.error(f"Error inspecting image {path}: {e}")
            return {
                "success": False,
                "error": f"Failed to inspect image: {str(e)}",
                "image_path": str(path),
            }

document_reader = DocumentReaderEngine()
