"""Shared rendering for observed tool results and streaming ACP content."""

from __future__ import annotations

import json
from typing import Any

_ACP_TOOL_CALL_CONTENT_TYPES = frozenset({"content", "diff", "terminal"})


def stringify_tool_payload(value: Any) -> str:
    """Render text, content-block lists and the ACP ToolCallContent union."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        if any(
            isinstance(block, dict)
            and isinstance(block.get("type"), str)
            and block["type"] in _ACP_TOOL_CALL_CONTENT_TYPES
            for block in value
        ):
            return "\n".join(_render_acp_tool_call_content(block) for block in value)
        text_parts = [
            block["text"]
            for block in value
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ]
        if text_parts:
            return "".join(text_parts)
    return _json_or_repr(value)


def _render_acp_tool_call_content(block: Any) -> str:
    """Render an ACP entry, naming non-text content instead of dumping its payload."""
    if isinstance(block, dict):
        block_type = block.get("type")
        if block_type == "content":
            inner = block.get("content")
            inner_blocks = [
                entry
                for entry in (inner if isinstance(inner, list) else [inner])
                if isinstance(entry, dict)
            ]
            texts = [entry["text"] for entry in inner_blocks if isinstance(entry.get("text"), str)]
            kinds = sorted(
                {
                    str(entry.get("type", "unknown"))
                    for entry in inner_blocks
                    if not isinstance(entry.get("text"), str)
                }
            )
            parts = ["".join(texts)] if texts else []
            if kinds:
                parts.append(f"[content: {', '.join(kinds)}]")
            if parts:
                return "\n".join(parts)
        elif block_type == "diff":
            path = block.get("path")
            new_text = block.get("newText")
            line_count = len(new_text.splitlines()) if isinstance(new_text, str) else 0
            count = f"{line_count} line" + ("" if line_count == 1 else "s")
            label = f"diff {path} ({count})" if path else f"diff ({count})"
            return f"{label}\n{new_text}" if isinstance(new_text, str) and new_text else label
        elif block_type == "terminal":
            terminal_id = block.get("terminalId")
            return f"[terminal {terminal_id}]" if terminal_id else "[terminal]"
        block_text = block.get("text")
        if isinstance(block_text, str):
            return block_text
    return _json_or_repr(block)


def _json_or_repr(value: Any) -> str:
    """Encode unknown payloads without losing non-JSON results."""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)
