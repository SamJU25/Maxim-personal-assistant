"""
TokenJuice In-Memory Tool Output Compression Engine for MaxIM.
Inspired by OpenHuman (tinyhumansai/openhuman).

Compresses tool outputs (JSON payloads, web text, process listings, file contents)
before they are injected into the ReAct LLM context window, saving up to 80% tokens.

Functional Core:
1. JSON Structural Minification: Strips nulls, empty collections, redundant envelopes,
   and minifies separators.
2. Markdown & Text Distillation: Strips repetitive whitespace, boilerplate navigation,
   and duplicate line breaks.
3. Tabular & List Compactor: Prunes high-volume repetitive rows (e.g. process lists),
   preserving high-signal headers and summaries.
4. Token Telemetry: Estimates token savings (characters / 4 rule-of-thumb) and tracks
   cumulative compression ratios.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("maxim.token_juice")


SCHEMA_KEYS_TO_PRESERVE = {"windows", "processes", "todos", "skills", "results", "channels", "mental_models", "dom_tree", "interactive_elements", "tabs"}

class TokenJuiceCompressor:
    def __init__(self, max_output_chars: int = 8000, enable_compression: bool = True):
        self.max_output_chars = max_output_chars
        self.enable_compression = enable_compression
        self.total_raw_chars = 0
        self.total_compressed_chars = 0

    def compress(self, raw_data: Union[str, Dict[str, Any], List[Any]], tool_name: Optional[str] = None) -> str:
        """
        Compresses raw tool output into a dense, token-efficient string representation.
        """
        if not self.enable_compression:
            return raw_data if isinstance(raw_data, str) else json.dumps(raw_data)

        # Convert to string or parse JSON
        raw_str = ""
        parsed_json: Optional[Any] = None

        if isinstance(raw_data, (dict, list)):
            parsed_json = raw_data
            raw_str = json.dumps(raw_data, indent=2)
        elif isinstance(raw_data, str):
            raw_str = raw_data
            # Attempt to parse as JSON if it looks like structured data
            clean_str = raw_str.strip()
            if (clean_str.startswith("{") and clean_str.endswith("}")) or (clean_str.startswith("[") and clean_str.endswith("]")):
                try:
                    parsed_json = json.loads(clean_str)
                except Exception:
                    parsed_json = None

        raw_len = len(raw_str)
        self.total_raw_chars += raw_len

        # Execute specialized compression based on data type and tool context
        if parsed_json is not None:
            compressed = self._compress_json(parsed_json, tool_name)
        else:
            compressed = self._compress_text(raw_str, tool_name)

        # Enforce hard ceiling if output is still excessively large
        if len(compressed) > self.max_output_chars:
            clipped_chars = len(compressed) - self.max_output_chars
            compressed = compressed[:self.max_output_chars] + f"\n... [TokenJuice clipped: {clipped_chars} chars truncated]"

        comp_len = len(compressed)
        self.total_compressed_chars += comp_len

        return compressed

    def _compress_json(self, data: Any, tool_name: Optional[str] = None) -> str:
        """Prunes nulls, empty collections, and unnecessary whitespace from JSON structures."""
        cleaned = self._prune_json_recursive(data)

        # If data is a list of repetitive items (e.g. process list or window list)
        if isinstance(cleaned, list) and len(cleaned) > 20:
            total_items = len(cleaned)
            cleaned = cleaned[:15]
            summary_item = {"_summary": f"... [{total_items - 15} additional items compacted by TokenJuice]"}
            cleaned.append(summary_item)
        elif isinstance(cleaned, dict):
            # If wrapped in a single key envelope like {"status": "success", "processes": [...]}, compact inner list
            for key, val in cleaned.items():
                if isinstance(val, list) and len(val) > 20:
                    total_items = len(val)
                    cleaned[key] = val[:15] + [{"_summary": f"... [{total_items - 15} items compacted]"}]

        # Compact JSON formatting (no indentation, tight separators)
        return json.dumps(cleaned, separators=(",", ":"), ensure_ascii=False)

    def _prune_json_recursive(self, item: Any) -> Any:
        """Recursively removes None values, empty lists/dicts, and cleans strings."""
        if isinstance(item, dict):
            pruned = {}
            for k, v in item.items():
                if v is None:
                    continue
                if isinstance(v, (dict, list)) and len(v) == 0 and k not in SCHEMA_KEYS_TO_PRESERVE:
                    continue
                pruned[k] = self._prune_json_recursive(v)
            return pruned
        elif isinstance(item, list):
            return [self._prune_json_recursive(elem) for elem in item if elem is not None]
        elif isinstance(item, str):
            # Clean excessive internal spaces or long base64 blobs
            if len(item) > 200 and re.match(r"^[A-Za-z0-9+/=]{200,}$", item.strip()):
                return f"[Base64 blob: {len(item)} bytes]"
            return item.strip()
        return item

    def _compress_text(self, text: str, tool_name: Optional[str] = None) -> str:
        """Compresses plain text and Markdown."""
        # 1. Normalize line endings
        s = text.replace("\r\n", "\n")

        # 2. Collapse 3+ consecutive newlines into 2
        s = re.sub(r"\n{3,}", "\n\n", s)

        # 3. Strip trailing/leading spaces on lines
        lines = [line.strip() for line in s.split("\n")]

        # 4. Remove empty or pure separator lines
        cleaned_lines = []
        for line in lines:
            if not line:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
            elif re.match(r"^[\-=*_]{4,}$", line):
                # Compress massive markdown divider lines
                cleaned_lines.append("---")
            else:
                # Collapse multi-spaces within lines
                compact_line = re.sub(r"[ \t]{2,}", " ", line)
                cleaned_lines.append(compact_line)

        return "\n".join(cleaned_lines).strip()

    def get_stats(self) -> Dict[str, Any]:
        """Returns cumulative token savings metrics."""
        raw_tokens = round(self.total_raw_chars / 4)
        comp_tokens = round(self.total_compressed_chars / 4)
        saved_tokens = max(0, raw_tokens - comp_tokens)
        ratio = round((1.0 - (comp_tokens / raw_tokens)) * 100, 1) if raw_tokens > 0 else 0.0

        return {
            "total_raw_characters": self.total_raw_chars,
            "total_compressed_characters": self.total_compressed_chars,
            "estimated_raw_tokens": raw_tokens,
            "estimated_compressed_tokens": comp_tokens,
            "tokens_saved": saved_tokens,
            "compression_ratio_percent": ratio,
        }

    def reset_stats(self):
        self.total_raw_chars = 0
        self.total_compressed_chars = 0


# Singleton instance
token_juice = TokenJuiceCompressor()
