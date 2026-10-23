"""Stockage documentaire minimal sur SQLite.

Huntboard manipule des « collections » de documents JSON (offers, notes, prep,
config), comme la base d'un artifact Claude. Ce module reproduit ce modèle :
une table unique (collection, id, data, version, updated_at), ce qui permet
d'utiliser la même interface web dans le kit Claude et dans l'application.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
  collection TEXT NOT NULL,
  id TEXT NOT NULL,
  data TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (collection, id)
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  summary TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class VersionConflict(Exception):
    """Le document a changé depuis la lecture du client."""


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # Lecture -----------------------------------------------------------
    def list(self, collection: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, data, version, updated_at FROM docs WHERE collection=? ORDER BY id",
                (collection,),
            ).fetchall()
        return [self._row(r) for r in rows]

    def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        with self._lock:
            r = self._conn.execute(
                "SELECT id, data, version, updated_at FROM docs WHERE collection=? AND id=?",
                (collection, doc_id),
            ).fetchone()
        return self._row(r) if r else None

    def data(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        d = self.get(collection, doc_id)
        return d["data"] if d else None

    # Écriture ----------------------------------------------------------
    def set(self, collection: str, doc_id: str, data: dict[str, Any], if_version: int | None = None) -> int:
        with self._lock:
            cur = self._conn.execute(
                "SELECT version FROM docs WHERE collection=? AND id=?", (collection, doc_id)
            ).fetchone()
            if cur and if_version is not None and cur["version"] != if_version:
                raise VersionConflict(f"{collection}/{doc_id} est à la version {cur['version']}")
            version = (cur["version"] + 1) if cur else 1
            self._conn.execute(
                "INSERT INTO docs(collection,id,data,version,updated_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(collection,id) DO UPDATE SET data=excluded.data, version=excluded.version, "
                "updated_at=excluded.updated_at",
                (collection, doc_id, json.dumps(data, ensure_ascii=False), version, now_iso()),
            )
            self._conn.commit()
            return version

    def update(self, collection: str, doc_id: str, patch: dict[str, Any], if_version: int | None = None) -> int:
        current = self.get(collection, doc_id)
        if current is None:
            raise KeyError(f"{collection}/{doc_id} n'existe pas")
        merged = _deep_merge(current["data"], patch)
        return self.set(collection, doc_id, merged, if_version=if_version if if_version is not None else current["version"])

    def delete(self, collection: str, doc_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM docs WHERE collection=? AND id=?", (collection, doc_id))
            self._conn.commit()

    # Journal des passages de veille ------------------------------------
    def start_run(self) -> int:
        with self._lock:
            c = self._conn.execute("INSERT INTO runs(started_at,status) VALUES(?, 'running')", (now_iso(),))
            self._conn.commit()
            return int(c.lastrowid)

    def finish_run(self, run_id: int, status: str, summary: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET finished_at=?, status=?, summary=? WHERE id=?",
                (now_iso(), status, summary, run_id),
            )
            self._conn.commit()

    def runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row(r: sqlite3.Row) -> dict[str, Any]:
        return {"id": r["id"], "data": json.loads(r["data"]), "version": r["version"], "updatedAt": r["updated_at"]}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in patch.items():
        if isinstance(v, dict) and v.get("__delete__") is True:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
