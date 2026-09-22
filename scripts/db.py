#!/usr/bin/env python3
"""
SQLite Storage & Indexing Engine for Room Speaker Calibration.
Provides ACID transactions, fast O(1) indexed session queries, and zero-dependency persistence.
"""
from __future__ import annotations

import os
import sqlite3
import json
import time
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("data/calibration.db")

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH) -> None:
    """Initializes tables and indexes."""
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                topology TEXT DEFAULT '2.1',
                profile_id TEXT DEFAULT 'harman_wide_room',
                points_count INTEGER DEFAULT 0,
                has_average INTEGER DEFAULT 0,
                metadata_json TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                point_num INTEGER NOT NULL,
                channel TEXT NOT NULL,
                snr_db REAL,
                rms_deviation_db REAL,
                peak_dbfs REAL,
                file_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_measurements_session ON measurements(session_id);")
        conn.commit()

def save_session(
    session_id: str,
    name: str,
    description: str = "",
    created_at: Optional[str] = None,
    topology: str = "2.1",
    profile_id: str = "harman_wide_room",
    points_count: int = 0,
    has_average: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    db_path: Path = DB_PATH,
) -> None:
    """Saves or updates a session in the database."""
    init_db(db_path)
    now_str = created_at or time.strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {})
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, name, description, created_at, topology, profile_id, points_count, has_average, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                points_count = excluded.points_count,
                has_average = excluded.has_average,
                metadata_json = excluded.metadata_json;
            """,
            (session_id, name, description, now_str, topology, profile_id, points_count, 1 if has_average else 0, meta_json),
        )
        conn.commit()

def record_measurement(
    session_id: str,
    point_num: int,
    channel: str,
    snr_db: float = 0.0,
    rms_deviation_db: float = 0.0,
    peak_dbfs: float = 0.0,
    file_path: str = "",
    db_path: Path = DB_PATH,
) -> None:
    """Records an individual channel measurement sweep."""
    init_db(db_path)
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO measurements (session_id, point_num, channel, snr_db, rms_deviation_db, peak_dbfs, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (session_id, point_num, channel, snr_db, rms_deviation_db, peak_dbfs, file_path, now_str),
        )
        conn.commit()

def list_sessions(limit: int = 50, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    """Returns indexed list of historical sessions ordered newest first."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, description, created_at, topology, profile_id, points_count, has_average, metadata_json FROM sessions ORDER BY created_at DESC LIMIT ?;",
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            meta = {}
            if r["metadata_json"]:
                try:
                    meta = json.loads(r["metadata_json"])
                except Exception:
                    pass
            result.append({
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "timestamp": r["created_at"],
                "points_count": r["points_count"],
                "points": meta.get("points", []),
                "has_average": bool(r["has_average"]),
                "topology": r["topology"],
                "profile_id": r["profile_id"],
                "metadata": meta,
            })
        return result

def sync_disk_sessions(sessions_dir: Path = Path("data/sessions"), db_path: Path = DB_PATH) -> int:
    """Syncs unindexed disk sessions into SQLite."""
    if not sessions_dir.exists():
        return 0
    init_db(db_path)
    synced = 0
    with get_connection(db_path) as conn:
        existing_ids = {r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()}
        for item in sessions_dir.iterdir():
            if item.is_dir() and item.name not in existing_ids:
                info_file = item / "session_info.json"
                if info_file.exists():
                    try:
                        info = json.loads(info_file.read_text(encoding="utf-8"))
                        s_id = info.get("id", item.name)
                        s_name = info.get("name", s_id)
                        s_desc = info.get("description", "")
                        s_time = info.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
                        pts = info.get("points", [])
                        has_avg = (item / "medicion_promedio_espacial.npz").exists()
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO sessions (id, name, description, created_at, points_count, has_average, metadata_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?);
                            """,
                            (s_id, s_name, s_desc, s_time, len(pts), 1 if has_avg else 0, json.dumps(info)),
                        )
                        synced += 1
                    except Exception as e:
                        print(f"[Aviso] No se pudo sincronizar sesión {item.name}: {e}")
        conn.commit()
    return synced

if __name__ == "__main__":
    init_db()
    count = sync_disk_sessions()
    print(f"[✓] SQLite Engine listo. {count} sesiones sincronizadas desde disco.")
    sessions = list_sessions(limit=5)
    print(f"Total sesiones indexadas: {len(sessions)}")
    for s in sessions:
        print(f" - [{s['timestamp']}] {s['id']}: {s['name']} ({s['points_count']} puntos)")
