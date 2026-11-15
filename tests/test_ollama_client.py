"""Offline client tests: no network, no Ollama installation necessary."""
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from io import BytesIO

import pytest

import ollama_client as oc


class FakeReply:
    def __init__(self, obj):
        self.body = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.body


def test_default_model_llama32(monkeypatch):
    monkeypatch.delenv('OLLAMA_MODEL', raising=False)
    assert oc.model_name() == 'llama3.2'


def test_list_installed_models():
    with patch.object(oc, '_request', return_value={'models': [{'name': 'llama3.2:latest'}, {'name': 'phi3:latest'}]}):
        assert oc.list_local_models() == ['llama3.2:latest', 'phi3:latest']
        assert 'llama3.2:latest' in oc.check_ollama_connection('llama3.2')


def test_no_models():
    with patch.object(oc, '_request', return_value={'models': []}):
        with pytest.raises(oc.RecipeAIError, match='ollama pull llama3.2'):
            oc.check_ollama_connection('llama3.2')


def test_model_json_parsing():
    assert oc._parse_model_json('{"chef_tips":["nice"]}') == {'chef_tips': ['nice']}
    assert oc._parse_model_json('```json\n{"x":2}\n```') == {'x': 2}
    assert oc._parse_model_json('Here is JSON {"x":3} done') == {'x': 3}
    with pytest.raises(oc.RecipeAIError):
        oc._parse_model_json('bad')


def test_local_chat_request_and_payload():
    def fake_request(path, payload=None, timeout=0):
        assert path == '/api/chat'
        assert payload['model'] == 'llama3.2'
        assert payload['format'] == 'json'
        assert payload['stream'] is False
        assert payload['messages'][0]['role'] == 'system'
        assert 'Paneer' in payload['messages'][1]['content']
        assert timeout == 300
        return {'message': {'content': '{"recipe_name":"Paneer Skillet"}'}}
    with patch.object(oc, '_request', side_effect=fake_request):
        result = oc.ask_ollama_json('Return recipe JSON', {'ingredients':['Paneer']}, max_tokens=1000, model='llama3.2')
    assert result['recipe_name'] == 'Paneer Skillet'


def test_retry_bad_json():
    with patch.object(oc, '_request', side_effect=[{'message':{'content':'nonsense'}}, {'message':{'content':'{"ok":true}'}}]) as call:
        assert oc.ask_ollama_json('Return JSON', {}, max_tokens=500) == {'ok':True}
        assert call.call_count == 2


def test_http_connection_error(monkeypatch):
    def bad(*args, **kwargs):
        raise URLError('refused')
    monkeypatch.setattr(oc, 'urlopen', bad)
    with pytest.raises(oc.RecipeAIError, match='Cannot reach Ollama'):
        oc.list_local_models()


def test_http_missing_model(monkeypatch):
    def bad(*args, **kwargs):
        raise HTTPError('http://127.0.0.1:11434/api/chat', 404, 'not found', {}, BytesIO(b'{"error":"model not found"}'))
    monkeypatch.setattr(oc, 'urlopen', bad)
    with pytest.raises(oc.RecipeAIError, match='could not find the model'):
        oc.ask_ollama_json('Return JSON', {})
