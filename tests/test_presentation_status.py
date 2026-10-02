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
