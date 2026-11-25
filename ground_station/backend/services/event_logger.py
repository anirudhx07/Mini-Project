"""SQLite-backed Mission Event Logger for COCKPIT."""

import csv
import io
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class EventLogger:
    """Thread-safe SQLite logger for system, ESP32, camera, and AI events."""

    def __init__(self, db_path: Path, socketio=None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._socketio = socketio
        self._init_db()

    def set_socketio(self, socketio):
        self._socketio = socketio

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mission_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        category TEXT NOT NULL,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        image_ref TEXT DEFAULT ''
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON mission_logs(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_cat ON mission_logs(category)")
                conn.commit()

    def log(
        self,
        category: str,
        message: str,
        level: str = "INFO",
        image_ref: str = "",
        broadcast: bool = True,
    ) -> Dict[str, Any]:
        """Persist an event and optionally broadcast it via WebSocket."""
        ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": ts,
            "category": category.upper(),
            "level": level.upper(),
            "message": message,
            "image_ref": image_ref or "",
        }
        with self._lock:
            with self._get_conn() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO mission_logs (timestamp, category, level, message, image_ref)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (entry["timestamp"], entry["category"], entry["level"], entry["message"], entry["image_ref"]),
                )
                entry["id"] = cur.lastrowid
                conn.commit()

        if broadcast and self._socketio is not None:
            try:
                self._socketio.emit("event_log", entry)
            except Exception:
                pass
        return entry

    def query(
        self,
        search: str = "",
        category: str = "",
        level: str = "",
        date_from: str = "",
        date_to: str = "",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Query mission logs with optional filters."""
        clauses = []
        params: List[Any] = []

        if search:
            clauses.append("(message LIKE ? OR image_ref LIKE ?)")
            like_q = f"%{search}%"
            params.extend([like_q, like_q])
        if category and category.upper() != "ALL":
            clauses.append("category = ?")
            params.append(category.upper())
        if level and level.upper() != "ALL":
            clauses.append("level = ?")
            params.append(level.upper())
        if date_from:
            clauses.append("timestamp >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("timestamp <= ?")
            params.append(f"{date_to} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT id, timestamp, category, level, message, image_ref FROM mission_logs {where_sql} ORDER BY id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 2000)))

        with self._lock:
            with self._get_conn() as conn:
                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]

    def clear(self) -> int:
        """Delete all mission log records and return deleted count."""
        with self._lock:
            with self._get_conn() as conn:
                cur = conn.execute("DELETE FROM mission_logs")
                deleted = cur.rowcount
                conn.commit()
                return deleted

    def export_csv(self, **filters) -> str:
        """Export filtered mission logs to CSV text."""
        rows = self.query(limit=2000, **filters)
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "timestamp", "category", "level", "message", "image_ref"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return output.getvalue()
