import asyncio
import ssl

import pytest

from app.api import routes
from app.core.http_client import worker_ssl_context


def test_worker_transport_keeps_certificate_and_hostname_verification():
    context = worker_ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


@pytest.mark.anyio
async def test_concurrent_visitors_share_one_worker_probe_and_short_cache(monkeypatch):
    monkeypatch.setattr(routes, "_ollama_status_cache", {})
    monkeypatch.setattr(routes.settings, "ollama_urls", "http://worker-a:11434,http://worker-b:11434")
    calls = []

    async def check(url):
        calls.append(url)
        await asyncio.sleep(0)
        return True

    monkeypatch.setattr(routes, "_check_ollama_worker", check)
    results = await asyncio.gather(*(routes._cached_ollama_checks() for _ in range(60)))
    assert results == [[True, True]] * 60
    assert len(calls) == 2
    assert await routes._cached_ollama_checks() == [True, True]
    assert len(calls) == 2


@pytest.mark.anyio
async def test_disconnected_visitor_does_not_cancel_other_visitors_probe(monkeypatch):
    monkeypatch.setattr(routes, "_ollama_status_cache", {})
    monkeypatch.setattr(routes.settings, "ollama_urls", "http://worker-a:11434")
    started, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def check(url):
        calls.append(url)
        started.set()
        await release.wait()
        return True

    monkeypatch.setattr(routes, "_check_ollama_worker", check)
    first = asyncio.create_task(routes._cached_ollama_checks())
    await started.wait()
    second = asyncio.create_task(routes._cached_ollama_checks())
    await asyncio.sleep(0)
    first.cancel()
    await asyncio.gather(first, return_exceptions=True)
    release.set()
    assert await second == [True]
    assert len(calls) == 1


@pytest.mark.anyio
async def test_worker_configuration_changes_and_expiry_refresh_readiness(monkeypatch):
    monkeypatch.setattr(routes, "_ollama_status_cache", {})
    monkeypatch.setattr(routes, "_SERVICE_STATUS_TTL_SECONDS", 0.01)
    monkeypatch.setattr(routes.settings, "ollama_urls", "http://worker-a:11434")
    calls = []

    async def check(url):
        calls.append(url)
        return len(calls) == 1

    monkeypatch.setattr(routes, "_check_ollama_worker", check)
    assert await routes._cached_ollama_checks() == [True]
    await asyncio.sleep(0.02)
    assert await routes._cached_ollama_checks() == [False]
    monkeypatch.setattr(routes.settings, "ollama_urls", "http://worker-b:11434")
    assert await routes._cached_ollama_checks() == [False]
    assert len(calls) == 3
