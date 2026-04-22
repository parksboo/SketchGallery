from __future__ import annotations

import json
from dataclasses import replace
from urllib.error import URLError

import pytest

from raycluster import callback as callback_module


class DummyResponse:
    def __init__(self, status=200, body=''):
        self.status = status
        self._body = body.encode('utf-8')

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_send_callback_posts_completed_payload(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['headers'] = dict(request.header_items())
        captured['payload'] = json.loads(request.data.decode('utf-8'))
        captured['timeout'] = timeout
        return DummyResponse(status=200)

    monkeypatch.setattr(callback_module, 'urlopen', fake_urlopen)
    monkeypatch.setattr(
        callback_module,
        "settings",
        replace(callback_module.settings, callback_timeout_sec=12, ray_shared_token=''),
    )

    callback_module.send_callback(
        callback_url='http://web/callback',
        callback_token='secret',
        status='completed',
        result_key='results/final.png',
    )

    assert captured['url'] == 'http://web/callback'
    assert captured['payload'] == {'status': 'completed', 'result_key': 'results/final.png'}
    assert captured['headers']['Authorization'] == 'Bearer secret'
    assert captured['timeout'] == 12


def test_send_callback_without_url_raises():
    with pytest.raises(callback_module.CallbackError, match='callback_url is empty'):
        callback_module.send_callback(
            callback_url='',
            callback_token='',
            status='completed',
            result_key='x',
        )


def test_send_callback_wraps_connection_errors(monkeypatch):
    monkeypatch.setattr(
        callback_module,
        'urlopen',
        lambda req, timeout: (_ for _ in ()).throw(URLError('boom')),
    )

    with pytest.raises(callback_module.CallbackError, match='connection error'):
        callback_module.send_callback(
            callback_url='http://web/callback',
            callback_token='',
            status='failed',
            error='boom',
        )
