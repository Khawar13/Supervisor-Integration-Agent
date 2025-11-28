"""
In-memory conversation tracking for chat context.

This is intentionally lightweight and per-process. For production, replace with
a persistent store (Redis/DB) and add TTLs or user scoping as needed.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# {conversation_id: [{"role": "user"/"assistant", "content": str}]}
_HISTORY: Dict[str, List[Dict[str, str]]] = {}


def get_history(conversation_id: str, limit: int = 6) -> List[Dict[str, str]]:
    """Return the most recent turns (user/assistant) for this conversation."""
    history = _HISTORY.get(conversation_id, [])
    if limit <= 0:
        return history
    return history[-limit:]


def append_turn(conversation_id: str, role: str, content: str) -> None:
    """Record a turn in the conversation."""
    _HISTORY.setdefault(conversation_id, []).append({"role": role, "content": content})
