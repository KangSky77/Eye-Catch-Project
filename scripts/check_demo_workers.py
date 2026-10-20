"""Wait for the configured local/VPN demo models without downloading anything."""
import argparse
import asyncio
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.core.http_client import worker_ssl_context


async def check(wait_seconds):
    if len(settings.ollama_url_list) < 5:
        print('The school demo configuration requires at least five AI workers.')
        return 1
    deadline = time.monotonic() + wait_seconds
    async with httpx.AsyncClient(timeout=5, verify=worker_ssl_context(), trust_env=False) as client:
        async def probe(url, photo=False):
            parts = urlsplit(url)
            endpoint = urlunsplit((parts.scheme, parts.netloc, '/readyz' if photo else '/api/ps', '', ''))
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
                if photo:
                    return data.get('status') == 'ready'
                return any(model.get('name') == settings.ollama_model
                           and model.get('size_vram', 0) >= model.get('size', 1) > 0
                           for model in data.get('models', []))
            except (httpx.HTTPError, ValueError, TypeError):
                return False

        while True:
            checks = await asyncio.gather(*(probe(url) for url in settings.ollama_url_list),
                                          *(probe(url, True) for url in settings.photo_worker_url_list))
            if all(checks):
                print(f'GPU models ready on all {len(settings.ollama_url_list)} AI workers; all configured remote photo APIs ready ({len(settings.photo_worker_url_list)}).')
                return 0
            if time.monotonic() >= deadline:
                print('Some demo workers are offline or their GPU models are not ready. Keep the PCs, Tailscale and AI servers running.')
                return 1
            print(f'Waiting for demo models: {sum(checks)}/{len(checks)} checks ready...', flush=True)
            await asyncio.sleep(min(5, max(0, deadline - time.monotonic())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait', type=float, default=120)
    args = parser.parse_args()
    if not 0 <= args.wait <= 300:
        parser.error('--wait must be between 0 and 300 seconds')
    raise SystemExit(asyncio.run(check(args.wait)))
