from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager, nullcontext

TABLES = (
    "source_state (source_id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    "releases (release_key TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    "report_versions (report_id TEXT NOT NULL, revision TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (report_id, revision))",
)


class Store:
    def __init__(self, sqlite_path, database_url=None):
        self.remote = bool(database_url)
        self.schema = "llm_reports." if self.remote else ""
        if self.remote:
            import psycopg

            self.connection = psycopg.connect(database_url, autocommit=True, connect_timeout=10)
        else:
            self.connection = sqlite3.connect(sqlite_path)
            with self.connection:
                for table in TABLES:
                    self.connection.execute(f"CREATE TABLE IF NOT EXISTS {table}")

    def execute(self, sql, parameters=()):
        query = sql.replace("?", "%s") if self.remote else sql
        return self.connection.execute(query, parameters)

    @contextmanager
    def lock(self):
        if self.remote:
            locked = self.execute("SELECT pg_try_advisory_lock(125522, 402)").fetchone()[0]
            if not locked:
                raise ValueError("Another report refresh is running")
        else:
            self.connection.execute("BEGIN IMMEDIATE")
        try:
            transaction = nullcontext() if self.remote else self.connection
            with transaction:
                yield self
        finally:
            self.connection.close()

    def source(self, name):
        row = self.execute(
            f"SELECT payload FROM {self.schema}source_state WHERE source_id = ?", (name,)
        ).fetchone()
        return json.loads(row[0]) if row else {}

    def releases(self):
        return [
            json.loads(row[0])
            for row in self.execute(f"SELECT payload FROM {self.schema}releases ORDER BY release_key")
        ]

    def save(self, rows, source=None, state=None):
        transaction = self.connection.transaction() if self.remote else nullcontext()
        with transaction:
            for row in rows:
                self.execute(
                    f"INSERT INTO {self.schema}releases VALUES (?, ?) "
                    "ON CONFLICT (release_key) DO UPDATE SET payload = excluded.payload",
                    (row["key"], json.dumps(row, sort_keys=True)),
                )
                report = row.get("report")
                if report and report.get("revision"):
                    self.execute(
                        f"INSERT INTO {self.schema}report_versions VALUES (?, ?, ?) "
                        "ON CONFLICT (report_id, revision) DO NOTHING",
                        (report["id"], report["revision"], json.dumps(report, sort_keys=True)),
                    )
            if source:
                self.execute(
                    f"INSERT INTO {self.schema}source_state VALUES (?, ?) "
                    "ON CONFLICT (source_id) DO UPDATE SET payload = excluded.payload",
                    (source, json.dumps(state, sort_keys=True)),
                )
