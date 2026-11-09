import sqlite3
from datetime import datetime
from pathlib import Path

from otopark.models import Visit

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    plate       TEXT NOT NULL,
    entry_time  TEXT NOT NULL,
    exit_time   TEXT
);
CREATE INDEX IF NOT EXISTS idx_visits_open_plate
    ON visits (plate) WHERE exit_time IS NULL;
"""


class VisitRepository:
    """Giriş-çıkış kayıtlarını SQLite veritabanında saklar."""

    def __init__(self, database: str | Path) -> None:
        self._connection = sqlite3.connect(database)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(_SCHEMA)

    def find_open_visit(self, plate: str) -> Visit | None:
        row = self._connection.execute(
            "SELECT * FROM visits WHERE plate = ? AND exit_time IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (plate,),
        ).fetchone()
        return _to_visit(row) if row else None

    def open_visit(self, plate: str, entry_time: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO visits (plate, entry_time) VALUES (?, ?)",
                (plate, entry_time.isoformat()),
            )

    def close_visit(self, visit_id: int, exit_time: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE visits SET exit_time = ? WHERE id = ?",
                (exit_time.isoformat(), visit_id),
            )

    def recent_visits(self, limit: int = 20) -> list[Visit]:
        rows = self._connection.execute(
            "SELECT * FROM visits ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_to_visit(row) for row in rows]

    def close(self) -> None:
        self._connection.close()


def _to_visit(row: sqlite3.Row) -> Visit:
    return Visit(
        id=row["id"],
        plate=row["plate"],
        entry_time=datetime.fromisoformat(row["entry_time"]),
        exit_time=datetime.fromisoformat(row["exit_time"]) if row["exit_time"] else None,
    )
