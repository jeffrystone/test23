import json
import sqlite3
from abc import ABC
from typing import Iterable

from .dto import Order


class AbstractOrderRepo(ABC):
    def insert_orders(self, orders: list[Order]) -> None:
        pass

    def check_unprocessed(self, ids: Iterable[str]) -> list[str]:
        pass


class SqlLiteDbOrderRepo(AbstractOrderRepo):

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def check_unprocessed(self, ids: Iterable[str]) -> list[str]:

        if not ids:
            return []

        placeholders = ",".join("?" * len(ids))

        cursor = self.conn.execute(
            f"SELECT project_id FROM orders WHERE project_id IN ({placeholders})",
            tuple(ids),
        )
        processed = {row[0] for row in cursor.fetchall()}
        return list(set(ids) - processed)

    def insert_orders(self, orders: list[Order]) -> None:
        if not orders:
            return

        data = [
            (
                order.id,  # project_id
                order.name,
                order.description,
                order.url,
                json.dumps(order.meta) if order.meta else None,
            )
            for order in orders
        ]

        self.conn.executemany(
            """
            INSERT INTO orders (project_id, name, description, url, meta)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                url=excluded.url,
                meta=excluded.meta
            """,
            data,
        )

        self.conn.commit()
