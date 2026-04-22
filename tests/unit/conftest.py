from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class FakeRepo:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.created_payloads: list[dict[str, Any]] = []
        self.completed_calls: list[tuple[str, str]] = []
        self.failed_calls: list[tuple[str, str]] = []
        self.processing_calls: list[str] = []
        self.deleted_calls: list[str] = []

    def init_schema(self) -> None:
        return None

    def create_job(self, **kwargs: Any) -> None:
        self.created_payloads.append(dict(kwargs))
        self.jobs[kwargs['job_id']] = {
            'id': kwargs['job_id'],
            'title': kwargs.get('title'),
            'prompt': kwargs.get('prompt'),
            'style': kwargs.get('style'),
            'sketch_name': kwargs.get('sketch_name'),
            'sketch_path': kwargs.get('sketch_path'),
            'result_path': kwargs.get('result_path'),
            'status': kwargs.get('status', 'queued'),
            'error': kwargs.get('error'),
            'created_at': kwargs.get('created_at'),
            'updated_at': kwargs.get('updated_at'),
        }

    def mark_processing(self, job_id: str) -> None:
        self.processing_calls.append(job_id)
        self.jobs[job_id]['status'] = 'processing'

    def mark_completed(self, job_id: str, result_path: str) -> None:
        self.completed_calls.append((job_id, result_path))
        self.jobs[job_id]['status'] = 'completed'
        self.jobs[job_id]['result_path'] = result_path
        self.jobs[job_id]['error'] = None

    def mark_failed(self, job_id: str, error: str) -> None:
        self.failed_calls.append((job_id, error))
        self.jobs[job_id]['status'] = 'failed'
        self.jobs[job_id]['error'] = error

    def get_job(self, job_id: str):
        return self.jobs.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        self.deleted_calls.append(job_id)
        return self.jobs.pop(job_id, None) is not None

    def list_completed_jobs(self, limit: int = 100):
        items = [row for row in self.jobs.values() if row.get('status') == 'completed']
        return items[:limit]

    def list_jobs(self, limit: int = 50):
        return list(self.jobs.values())[:limit]

    def stats(self):
        rows = list(self.jobs.values())
        return {
            'total': len(rows),
            'completed': sum(1 for r in rows if r.get('status') == 'completed'),
            'processing': sum(1 for r in rows if r.get('status') == 'processing'),
            'queued': sum(1 for r in rows if r.get('status') == 'queued'),
        }


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, fake_repo: FakeRepo):
    import webserver.app as web_app

    monkeypatch.setattr(web_app, 'PostgresRepository', lambda: fake_repo)
    app = web_app.create_app()
    app.config.update(TESTING=True)
    app.extensions['repo'] = fake_repo
    return app


@pytest.fixture
def client(app):
    return app.test_client()
