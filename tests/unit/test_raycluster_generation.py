from __future__ import annotations

import pytest

from ray.exceptions import GetTimeoutError

from raycluster import generation


def test_build_generation_prompt_includes_title_prompt_and_style():
    prompt = generation.build_generation_prompt(
        title='Castle',
        user_prompt='on a snowy cliff',
        style='Fantasy Matte',
    )

    assert 'Castle' in prompt
    assert 'on a snowy cliff' in prompt
    assert 'Fantasy Matte' in prompt
    assert 'magical ambience' in prompt


def test_run_generation_sends_completed_callback(monkeypatch):
    monkeypatch.setattr(generation, '_ensure_ray_initialized', lambda: None)

    class DummyRemote:
        def remote(self, **kwargs):
            return 'obj-ref'

    monkeypatch.setattr(generation, 'generate_image_remote', DummyRemote())
    monkeypatch.setattr(generation.ray, 'get', lambda obj_ref, timeout: {'result_key': 'results/final.png'})

    sent = {}
    monkeypatch.setattr(generation, 'send_callback', lambda **kwargs: sent.update(kwargs))

    generation.run_generation(
        sketch_key='sketches/input.png',
        result_key='results/original.png',
        callback_url='http://callback',
        callback_token='secret',
        final_prompt='prompt',
        mode='hf',
    )

    assert sent['status'] == 'completed'
    assert sent['result_key'] == 'results/final.png'
    assert sent['callback_url'] == 'http://callback'


def test_run_generation_timeout_marks_failed(monkeypatch):
    monkeypatch.setattr(generation, '_ensure_ray_initialized', lambda: None)

    class DummyRemote:
        def remote(self, **kwargs):
            return 'obj-ref'

    monkeypatch.setattr(generation, 'generate_image_remote', DummyRemote())
    monkeypatch.setattr(generation.ray, 'get', lambda obj_ref, timeout: (_ for _ in ()).throw(GetTimeoutError()))

    failed = {}
    monkeypatch.setattr(generation, '_try_failed_callback', lambda **kwargs: failed.update(kwargs))

    with pytest.raises(generation.GenerationError, match='timed out'):
        generation.run_generation(
            sketch_key='sketches/input.png',
            result_key='results/original.png',
            callback_url='http://callback',
            callback_token='secret',
            final_prompt='prompt',
            mode='hf',
        )

    assert 'timeout after' in failed['error']


def test_call_api_requires_token(monkeypatch):
    monkeypatch.setattr(generation.settings, 'hf_token_env', 'HF_TOKEN')
    monkeypatch.delenv('HF_TOKEN', raising=False)

    with pytest.raises(generation.GenerationError, match='missing Hugging Face token env'):
        generation._call_api(
            sketch_key='sketches/input.png',
            result_key='results/out.png',
            final_prompt='prompt',
        )
