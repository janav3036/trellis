import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime

class Ingester(ABC):
    def __init__(self, db_path:str):
        self.db_path = db_path

    @abstractmethod
    def run(self) -> int:
        """Fetch recent data and insert new events. Return count inserted"""

    @abstractmethod
    def backfill(self, start_date: datetime) -> int:
        """Fetch historical data from start_date to now. Returns count inserted"""

    def _insert_event(
            self, 
            conn: sqlite3.Connection, 
            timestamp: datetime, 
            source: str, 
            event_type: str, 
            metadata: dict
    ) -> int:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO events (timestamp, source, event_type, metadata)
            VALUES(?,?,?,?)
            """,
            (timestamp.isoformat(), source, event_type, json.dumps(metadata))
        )
        return cur.rowcount
