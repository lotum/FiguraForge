"""Credential helper must keep secrets local and avoid replacing existing keys."""
import importlib.util
from pathlib import Path
import httpx
import pytest

spec = importlib.util.spec_from_file_location('key_from_clipboard',
    Path(__file__).parents[1] / 'scripts/key_from_clipboard.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def test_clipboard_helper_only_stores_locally(capsys):
    calls = []
    def handle(request):
        calls.append(request)
        assert request.url.host == '127.0.0.1'
        if request.url.path == '/api/config':
            return httpx.Response(200, json={'providers': {'meshy': False}})
        assert request.url.path == '/api/secrets'
        assert b'canary-copied-key' in request.content
        return httpx.Response(200, json={'meshy': True})
    with httpx.Client(base_url='http://127.0.0.1:8000', transport=httpx.MockTransport(handle)) as client:
        helper.store_key('meshy', clipboard='canary-copied-key\n', client=client)
    assert len(calls) == 2
    assert 'canary-copied-key' not in capsys.readouterr().out


def test_clipboard_helper_preserves_existing_key():
    def handle(request):
        assert request.method == 'GET'
        return httpx.Response(200, json={'providers': {'openai': True}})
    with httpx.Client(base_url='http://127.0.0.1:8000', transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match='bereits konfiguriert'):
            helper.store_key('openai', clipboard='new-canary-key', client=client)


def test_clipboard_helper_rejects_multiline_before_network():
    with pytest.raises(ValueError, match='nur den API-Key'):
        helper.store_key('meshy', clipboard='canary-key\nsecond-secret')


def test_clipboard_helper_uses_real_encrypted_vault(client):
    helper.store_key('meshy', clipboard='canary-test-only-key', client=client)
    assert client.app.state.vault.get('meshy') == 'canary-test-only-key'
    assert b'canary-test-only-key' not in client.app.state.vault.file.read_bytes()


def test_clipboard_helper_replaces_only_when_explicit(client):
    client.app.state.vault.set('openai', 'old-canary-test-key')
    helper.store_key('openai', clipboard='new-canary-test-key', client=client, replace=True)
    assert client.app.state.vault.get('openai') == 'new-canary-test-key'
    assert b'new-canary-test-key' not in client.app.state.vault.file.read_bytes()
