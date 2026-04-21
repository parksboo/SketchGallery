from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

from webserver.config import settings


class PostgresRepository:
    def __init__(self) -> None:
        self._dsn = settings.database_url or (
            f"host={settings.pg_host} "
            f"port={settings.pg_port} "
            f"dbname={settings.pg_db} "
            f"user={settings.pg_user} "
            f"password={settings.pg_password}"
        )

    @contextmanager
    def conn(self):
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            yield connection

    def init_schema(self) -> None:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id UUID PRIMARY KEY,
                    title TEXT,
                    prompt TEXT,
                    style TEXT,
                    sketch_name TEXT,
                    sketch_path TEXT NOT NULL,
                    result_path TEXT,
                    status VARCHAR(32) NOT NULL,
                    error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS style TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS sketch_name TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS prompt TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS sketch_path TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS result_path TEXT")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status VARCHAR(32)")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS error TEXT")
            cur.execute(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            )
            cur.execute(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC)")
            con.commit()

    def create_job(
        self,
        job_id: str,
        title: str,
        prompt: str,
        style: str,
        sketch_name: str,
        sketch_path: str,
        result_path: str,
        status: str,
    ) -> None:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs
                (id, title, prompt, style, sketch_name, sketch_path, result_path, status, error, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NOW(), NOW())
                """,
                (job_id, title, prompt, style, sketch_name, sketch_path, result_path, status),
            )
            con.commit()

    def mark_processing(self, job_id: str) -> None:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                UPDATE jobs
                SET status = 'processing', error = NULL, updated_at = NOW()
                WHERE id = %s
                """,
                (job_id,),
            )
            con.commit()

    def mark_completed(self, job_id: str, result_path: str) -> None:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                UPDATE jobs
                SET status = 'completed', result_path = %s, error = NULL, updated_at = NOW()
                WHERE id = %s
                """,
                (result_path, job_id),
            )
            con.commit()

    def mark_failed(self, job_id: str, error: str) -> None:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                UPDATE jobs
                SET status = 'failed', error = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (error, job_id),
            )
            con.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.conn() as con, con.cursor() as cur:
            cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            return cur.fetchone()

    def delete_job(self, job_id: str) -> bool:
        with self.conn() as con, con.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            deleted = cur.rowcount > 0
            con.commit()
            return deleted

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM jobs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    def list_completed_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM jobs
                WHERE status = 'completed'
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    def stats(self) -> Dict[str, int]:
        with self.conn() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                  COUNT(*) FILTER (WHERE status = 'processing') AS processing,
                  COUNT(*) FILTER (WHERE status = 'queued') AS queued
                FROM jobs
                """
            )
            row = cur.fetchone() or {}
            return {
                "total": int(row.get("total", 0)),
                "completed": int(row.get("completed", 0)),
                "processing": int(row.get("processing", 0)),
                "queued": int(row.get("queued", 0)),
            }
