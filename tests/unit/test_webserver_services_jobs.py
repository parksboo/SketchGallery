from __future__ import annotations

from webserver.services import jobs as jobs_service


def test_to_ui_job_generates_signed_urls_and_progress(monkeypatch):
    monkeypatch.setattr(jobs_service, 'issue_download_url', lambda key: f'https://signed/{key}')

    row = {
        'id': 'job-1',
        'title': 'My Art',
        'prompt': 'mountain',
        'style': 'Cinematic',
        'sketch_name': 'input.png',
        'sketch_path': 'sketches/input.png',
        'result_path': 'results/job-1.png',
        'status': 'completed',
    }

    payload = jobs_service.to_ui_job(row)

    assert payload['id'] == 'job-1'
    assert payload['sketch_url'] == 'https://signed/sketches/input.png'
    assert payload['generated_url'] == 'https://signed/results/job-1.png'
    assert payload['progress'] == 100


def test_to_api_job_omits_error_and_result_for_incomplete_job(monkeypatch):
    monkeypatch.setattr(jobs_service, 'issue_download_url', lambda key: f'https://signed/{key}')
    row = {
        'id': 'job-2',
        'title': 'Queued',
        'prompt': 'forest',
        'style': 'Illustration',
        'status': 'processing',
        'sketch_path': 'sketches/input.png',
        'result_path': 'results/job-2.png',
        'created_at': None,
        'updated_at': None,
    }

    payload = jobs_service.to_api_job(row)

    assert payload['job_id'] == 'job-2'
    assert payload['sketch_url'] == 'https://signed/sketches/input.png'
    assert payload['result_url'] == 'https://signed/results/job-2.png'
    assert 'error' not in payload


def test_select_featured_wraps_prev_and_next():
    items = [
        {'id': 'a'},
        {'id': 'b'},
        {'id': 'c'},
    ]

    featured, prev_item, next_item = jobs_service.select_featured(items, 'a')

    assert featured == {'id': 'a'}
    assert prev_item == {'id': 'c'}
    assert next_item == {'id': 'b'}
