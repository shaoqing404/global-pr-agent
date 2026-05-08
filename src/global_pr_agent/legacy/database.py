from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional

from .models import BrandProfile


def get_default_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "storage/pr_agent.db")


class BrandRepository:
    """Simple SQLite repository for brand profiles."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or get_default_db_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS brand_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_name TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def upsert(self, profile: BrandProfile) -> None:
        payload = json.dumps(profile.to_dict(), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO brand_profiles (brand_name, payload)
                VALUES (?, ?)
                ON CONFLICT(brand_name) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (profile.brand_name, payload),
            )
            conn.commit()

    def list_profiles(self) -> List[BrandProfile]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM brand_profiles ORDER BY updated_at DESC"
            ).fetchall()
        return [BrandProfile(**json.loads(row[0])) for row in rows]

    def get(self, brand_name: str) -> Optional[BrandProfile]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM brand_profiles WHERE brand_name = ?",
                (brand_name,),
            ).fetchone()
        if not row:
            return None
        return BrandProfile(**json.loads(row[0]))

    def delete(self, brand_name: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM brand_profiles WHERE brand_name = ?", (brand_name,))
            conn.commit()
            return cur.rowcount > 0
