"""Gestor SQLite para el historial y los ajustes de la aplicación."""

import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """Proporciona acceso thread-safe a la base de datos local."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.expanduser("~"), "media_downloader.db")

        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    format TEXT,
                    quality TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_path TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                ("default_format", "mp4"),
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                ("max_concurrent", "2"),
            )

    def add_download(self, download: Dict[str, Any]) -> bool:
        """Inserta o actualiza un registro del historial."""
        required = ("id", "title", "url")
        if any(download.get(key) is None for key in required):
            return False

        values = (
            download["id"],
            download["title"],
            download["url"],
            download.get("format"),
            download.get("quality"),
            download.get("file_size", 0),
            download.get("file_path"),
            download.get("status"),
        )
        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO downloads
                        (id, title, url, format, quality, file_size, file_path, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        url = excluded.url,
                        format = excluded.format,
                        quality = excluded.quality,
                        file_size = excluded.file_size,
                        file_path = excluded.file_path,
                        status = excluded.status
                    """,
                    values,
                )
            return True
        except sqlite3.Error as error:
            print(f"[Database] Error guardando descarga: {error}")
            return False

    def get_download_by_id(self, download_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM downloads WHERE id = ?", (download_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_all_downloads(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM downloads ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_download(self, download_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM downloads WHERE id = ?", (download_id,)
            )
        return cursor.rowcount > 0

    def clear_history(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM downloads")

    def get_setting(self, key: str, default: str = "") -> str:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
