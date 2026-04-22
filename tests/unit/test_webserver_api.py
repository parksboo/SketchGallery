from __future__ import annotations

import uuid

import pytest

from webserver.routes import api as api_routes


def test_create_job_success(client, fake_repo, monkeypatch):
    monkeypatch.setattr(api_routes, 'dispatch_generation_job', lambda **kwargs: {'accepted': True})
    monkeypatch.setattr(uuid, 'uuid4', lambda: '11111111-1111-1111-1111-111111111111')

    response = client.post(
        '/api/v1/jobs',
        json={
            'sketch_key': 'sketches/input.png',
            'title': 'Test title',
            'prompt': 'Test prompt',
            'style': 'Cinematic',
            'mode': 'test',
        },
    )

    assert response.status_code == 202
    assert response.get_json() == {
        'job_id': '11111111-1111-1111-1111-111111111111',
        'status': 'processing',
    }
    assert fake_repo.jobs['11111111-1111-1111-1111-111111111111']['status'] == 'processing'


def test_create_job_marks_failed_when_dispatch_fails(client, fake_repo, monkeypatch):
    def boom(**kwargs):
        raise api_routes.GenerationDispatchError('dispatch failed')

    monkeypatch.setattr(api_routes, 'dispatch_generation_job', boom)
    monkeypatch.setattr(uuid, 'uuid4', lambda: '22222222-2222-2222-2222-222222222222')

    response = client.post('/api/v1/jobs', json={'sketch_key': 'sketches/input.png'})

    assert response.status_code == 502
    assert response.get_json()['status'] == 'failed'
    assert fake_repo.jobs['22222222-2222-2222-2222-222222222222']['status'] == 'failed'


def test_sign_upload_returns_payload(client, monkeypatch):
    monkeypatch.setattr(api_routes, 'issue_upload_url', lambda filename, purpose='sketches': {
        'upload_url': 'https://upload',
        'object_key': 'sketches/abc.png',
        'content_type': 'image/png',
        'expires_in': '600',
    })

    response = client.post('/api/v1/uploads/sign', json={'filename': 'test.png', 'purpose': 'sketches'})

    assert response.status_code == 200
    assert response.get_json()['object_key'] == 'sketches/abc.png'


def test_ray_job_result_marks_completed(client, fake_repo):
    fake_repo.create_job(
        job_id='job-1', title='x', prompt='y', style='Cinematic', sketch_name='upload.png',
        sketch_path='sketches/input.png', result_path='results/job-1.png', status='processing'
    )

    response = client.post(
        '/api/v1/internal/ray/jobs/job-1/result',
        json={'status': 'completed', 'result_key': 'results/final.png'},
    )

    assert response.status_code == 200
    assert fake_repo.jobs['job-1']['status'] == 'completed'
    assert fake_repo.jobs['job-1']['result_path'] == 'results/final.png'


def test_ray_job_result_marks_failed(client, fake_repo):
    fake_repo.create_job(
        job_id='job-2', title='x', prompt='y', style='Cinematic', sketch_name='upload.png',
        sketch_path='sketches/input.png', result_path='results/job-2.png', status='processing'
    )

    response = client.post(
        '/api/v1/internal/ray/jobs/job-2/result',
        json={'status': 'failed', 'error': 'boom'},
    )

    assert response.status_code == 200
    assert fake_repo.jobs['job-2']['status'] == 'failed'
    assert fake_repo.jobs['job-2']['error'] == 'boom'
