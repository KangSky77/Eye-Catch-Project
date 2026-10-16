import pytest
import httpx
from app.api import routes


@pytest.mark.parametrize('photo,model_present,expected', [(True,True,200),(False,True,503),(True,False,503)])
def test_service_status_checks_model_and_photo_without_database(client, monkeypatch, photo, model_present, expected):
    monkeypatch.setattr(routes.vision,'weights_loaded',photo)
    monkeypatch.setattr(routes.eye_detector,'is_ready',lambda: True)
    monkeypatch.setattr(routes.eye_validator,'is_ready',lambda: True)
    class FakeClient:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def get(self,url):
            return httpx.Response(200,request=httpx.Request('GET',url),json={
                'models':[{'name':routes.settings.ollama_model}] if model_present else []})
    monkeypatch.setattr(routes.httpx,'AsyncClient',FakeClient)
    response=client.get('/api/service-status')
    assert response.status_code==expected
    assert 'storage' not in response.json()['services']
    assert 'localhost' not in response.text


def test_status_handles_ollama_network_failure(client,monkeypatch):
    monkeypatch.setattr(routes.vision,'weights_loaded',True)
    monkeypatch.setattr(routes.eye_detector,'is_ready',lambda:True)
    monkeypatch.setattr(routes.eye_validator,'is_ready',lambda:True)
    class Offline:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): raise httpx.ConnectError('secret-host')
        async def __aexit__(self,*args): pass
    monkeypatch.setattr(routes.httpx,'AsyncClient',Offline)
    response=client.get('/api/service-status')
    assert response.status_code==503
    assert response.json()['services']['ollama']=='unavailable'
    assert 'secret-host' not in response.text


def test_status_succeeds_when_one_of_multiple_ollama_workers_is_ready(client, monkeypatch):
    monkeypatch.setattr(routes.vision, 'weights_loaded', True)
    monkeypatch.setattr(routes.eye_detector, 'is_ready', lambda: True)
    monkeypatch.setattr(routes.eye_validator, 'is_ready', lambda: True)
    monkeypatch.setattr(routes.settings, 'ollama_urls', 'http://100.64.0.1:11434,http://100.64.0.2:11434')
    class MixedPool:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url):
            if '100.64.0.1' in url:
                raise httpx.ConnectError('worker-1-down')
            return httpx.Response(200, request=httpx.Request('GET', url), json={
                'models': [{'name': routes.settings.ollama_model}]})
    monkeypatch.setattr(routes.httpx, 'AsyncClient', MixedPool)
    response = client.get('/api/service-status')
    assert response.status_code == 200
    assert response.json()['services']['ollama'] == 'ready'
    assert '100.64' not in response.text


def test_photo_worker_failure_falls_back_to_local_inference(client, monkeypatch):
    from tests.conftest import make_image_bytes
    routes.reset_photo_worker_pool_state()
    monkeypatch.setattr(routes.settings, 'photo_worker_urls', 'http://100.64.0.9:8003')
    routes._photo_rr_cursor = 1  # force remote worker first
    class BrokenWorker:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            raise httpx.ConnectError('remote photo worker down')
    monkeypatch.setattr(routes.httpx, 'AsyncClient', BrokenWorker)
    monkeypatch.setattr(routes, 'predict_cataract', lambda img: {
        'probability': 1.5, 'result': '정상', 'result_code': 'normal', 'mode': 'eye',
        'eyes_detected': 0, 'eye_probs': [1.5], 'eyes': [{'side': 'single', 'probability': 1.5, 'code': 'normal'}],
        'asymmetric': False,
    })
    r = client.post('/api/analyze-eye', files={'file': ('e.jpg', make_image_bytes(), 'image/jpeg')})
    assert r.status_code == 200
    assert r.json()['result_code'] == 'normal'
    routes.reset_photo_worker_pool_state()

