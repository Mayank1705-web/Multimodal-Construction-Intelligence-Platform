"""SQLite persistence for analysis history ("Data Storage" in the architecture)."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from .config import get_settings

_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(get_settings().data_path / "platform.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            request_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            provider TEXT NOT NULL
        )"""
    )
    return conn


def save(kind: str, title: str, request: dict[str, Any], result: dict[str, Any], provider: str) -> int:
    with _lock, _conn() as c:
        cur = c.execute(
            "INSERT INTO analyses (kind, created_at, title, request_json, result_json, provider) VALUES (?,?,?,?,?,?)",
            (kind, datetime.now(timezone.utc).isoformat(timespec="seconds"), title[:140],
             json.dumps(request, default=str), json.dumps(result, default=str), provider),
        )
        return int(cur.lastrowid)


def list_items(kind: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    q = "SELECT id, kind, created_at, title, provider FROM analyses"
    args: list[Any] = []
    if kind:
        q += " WHERE kind = ?"
        args.append(kind)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(max(1, min(limit, 200)))
    with _lock, _conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def get(item_id: int) -> Optional[dict[str, Any]]:
    with _lock, _conn() as c:
        r = c.execute("SELECT * FROM analyses WHERE id = ?", (item_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["request"] = json.loads(d.pop("request_json"))
    d["result"] = json.loads(d.pop("result_json"))
    return d


def delete(item_id: int) -> bool:
    with _lock, _conn() as c:
        return c.execute("DELETE FROM analyses WHERE id = ?", (item_id,)).rowcount > 0
