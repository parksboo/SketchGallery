from __future__ import annotations

import json
from dataclasses import replace
from urllib.error import URLError

import pytest

from webserver.services import generation as generation_service


class DummyResponse:
    def __init__(self, status=202, body='{"ok": true}'):
        self.status = status
        self._body = body.encode('utf-8')

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dispatch_generation_job_builds_payload_and_headers(monkeypatch):
    monkeypatch.setattr(
        generation_service,
        "settings",
        replace(
            generation_service.settings,
            ray_generation_url="http://ray/generate",
            web_public_base_url="http://web:5050",
            ray_shared_token="shared-secret",
            ray_request_timeout_sec=7,
        ),
    )

    captured = {}

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['timeout'] = timeout
        captured['headers'] = dict(request.header_items())
        captured['payload'] = json.loads(request.data.decode('utf-8'))
        return DummyResponse(status=202, body='{"accepted": true}')

    monkeypatch.setattr(generation_service, 'urlopen', fake_urlopen)

    result = generation_service.dispatch_generation_job(
        job_id='job-1',
        sketch_key='sketches/input.png',
        result_key='results/job-1.png',
        title='Title',
        prompt='Prompt',
        style='Cinematic',
        mode='hf',
    )

    assert result == {'accepted': True}
    assert captured['url'] == 'http://ray/generate'
    assert captured['timeout'] == 7
    assert captured['payload']['callback_url'].endswith('/api/v1/internal/ray/jobs/job-1/result')
    assert captured['payload']['callback_token'] == 'shared-secret'
    assert captured['payload']['mode'] == 'hf'
    assert captured['headers']['Authorization'] == 'Bearer shared-secret'


def test_dispatch_generation_job_requires_endpoint(monkeypatch):
    monkeypatch.setattr(
        generation_service,
        "settings",
        replace(generation_service.settings, ray_generation_url=""),
    )

    with pytest.raises(generation_service.GenerationDispatchError):
        generation_service.dispatch_generation_job(
            job_id='job-1',
            sketch_key='sketches/input.png',
            result_key='results/job-1.png',
            title='Title',
            prompt='Prompt',
            style='Cinematic',
            mode='test',
        )


def test_dispatch_generation_job_wraps_url_errors(monkeypatch):
    monkeypatch.setattr(
        generation_service,
        "settings",
        replace(generation_service.settings, ray_generation_url="http://ray/generate"),
    )
    monkeypatch.setattr(
        generation_service,
        'urlopen',
        lambda request, timeout: (_ for _ in ()).throw(URLError('boom')),
    )

    with pytest.raises(generation_service.GenerationDispatchError, match='connection error'):
        generation_service.dispatch_generation_job(
            job_id='job-1',
            sketch_key='sketches/input.png',
            result_key='results/job-1.png',
            title='Title',
            prompt='Prompt',
            style='Cinematic',
            mode='test',
        )

