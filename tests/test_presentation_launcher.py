import httpx
import pytest
from scripts import start_presentation as launcher


class Client:
    def __init__(self, *args, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass


@pytest.mark.parametrize('payload', [[], {}, {'services': {'photo': 'ready', 'ollama': 'ready'}},
                                    {'status': 'ready', 'services': {'photo': 'invalid', 'ollama': 'ready'}}])
def test_unrelated_json_service_is_not_treated_as_eye_catch(payload):
    class OtherService:
        def get(self, url):
            return httpx.Response(200, json=payload, request=httpx.Request('GET', url))
    assert launcher.get_status(OtherService(), 'http://127.0.0.1:8001') is None


def test_busy_port_never_stops_or_replaces_another_service(monkeypatch):
    monkeypatch.setattr(launcher.sys, 'argv', ['start_presentation.py'])
    monkeypatch.setattr(launcher.httpx, 'Client', Client)
    monkeypatch.setattr(launcher, 'get_status', lambda *args: None)
    monkeypatch.setattr(launcher, 'port_available', lambda *args: False)
    monkeypatch.setattr(launcher, 'launch', lambda *args: (_ for _ in ()).throw(AssertionError('must not start')))
    assert launcher.main() == 1


def test_ready_server_is_reused_without_second_server(monkeypatch):
    monkeypatch.setattr(launcher.sys, 'argv', ['start_presentation.py'])
    monkeypatch.setattr(launcher.httpx, 'Client', Client)
    monkeypatch.setattr(launcher, 'get_status', lambda *args: {'status':'ready','services':{'photo':'ready','ollama':'ready'}})
    monkeypatch.setattr(launcher, 'ensure_ollama', lambda *args: None)
    monkeypatch.setattr(launcher, 'launch', lambda *args: (_ for _ in ()).throw(AssertionError('duplicate server')))
    assert launcher.main() == 0


def test_remote_ollama_failure_does_not_launch_local_substitute(monkeypatch):
    monkeypatch.setattr(launcher.settings, 'ollama_url', 'https://remote.example/api/generate')
    class Offline:
        def get(self, url): raise httpx.ConnectError('offline')
    monkeypatch.setattr(launcher, 'launch', lambda *args: (_ for _ in ()).throw(AssertionError('remote configuration')))
    launcher.ensure_ollama(Offline())


def test_ollama_launch_binds_loopback_on_configured_port(monkeypatch):
    monkeypatch.setattr(launcher.settings, 'ollama_url', 'http://127.0.0.1:11435/api/generate')
    monkeypatch.setenv('OLLAMA_HOST', '0.0.0.0:11434')
    monkeypatch.setattr(launcher.shutil, 'which', lambda name: 'ollama.exe')
    calls=[]
    monkeypatch.setattr(launcher, 'launch', lambda *args: calls.append(args))
    class StartsLater:
        def __init__(self): self.calls=0
        def get(self,url):
            self.calls+=1
            if self.calls==1: raise httpx.ConnectError('offline')
            return httpx.Response(200,request=httpx.Request('GET',url))
    launcher.ensure_ollama(StartsLater())
    assert calls[0][0] == ['ollama.exe','serve']
    assert calls[0][2]['OLLAMA_HOST'] == '127.0.0.1:11435'
