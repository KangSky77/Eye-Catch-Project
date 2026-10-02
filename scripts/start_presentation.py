"""Start local Eye-Catch and local Ollama without downloading models or killing processes."""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.config import settings


def get_status(client, url):
    try:
        response = client.get(url + '/api/service-status')
        if response.status_code not in (200, 503):
            return None
        data = response.json()
        if not isinstance(data, dict) or data.get('status') not in ('ready', 'degraded'):
            return None
        services = data.get('services')
        if not isinstance(services, dict) or any(services.get(name) not in ('ready', 'unavailable')
                                                 for name in ('photo', 'ollama')):
            return None
        return data
    except (httpx.HTTPError, ValueError):
        return None


def launch(command, log_name, env=None):
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    with (ROOT / log_name).open('ab') as log:
        return subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log,
                                stdin=subprocess.DEVNULL, creationflags=flags, env=env)


def ensure_ollama(client):
    parts = urlsplit(settings.ollama_url)
    tags = urlunsplit((parts.scheme, parts.netloc, '/api/tags', '', ''))
    try:
        response = client.get(tags)
        response.raise_for_status()
        return
    except httpx.HTTPError:
        pass
    if parts.scheme != 'http' or parts.hostname not in ('localhost', '127.0.0.1', '::1'):
        print('Configured Ollama is unavailable. Check the configured server; no local substitute was started.')
        return
    executable = shutil.which('ollama')
    if not executable:
        print('Ollama executable not found. Install Ollama and the configured model before presenting.')
        return
    task_env = os.environ.copy()
    # Bind only to loopback, on the configured port, even if the user's shell exposes OLLAMA_HOST.
    loopback = '[::1]' if parts.hostname == '::1' else '127.0.0.1'
    task_env['OLLAMA_HOST'] = f'{loopback}:{parts.port or 11434}'
    process = launch([executable, 'serve'], 'presentation-ollama.log', task_env)
    for _ in range(20):
        try:
            client.get(tags).raise_for_status()
            print('Ollama is running.')
            return
        except httpx.HTTPError:
            if process.poll() is not None:
                break
            time.sleep(.5)
    print('Ollama did not become ready. See presentation-ollama.log.')


def port_available(port):
    try:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    base = f'http://127.0.0.1:{args.port}'
    with httpx.Client(timeout=5, trust_env=False) as client:
        existing = get_status(client, base)
        if not existing and not port_available(args.port):
            print(f'Port {args.port} belongs to another service. Nothing was stopped. Choose --port.')
            return 1
        ensure_ollama(client)
        if not existing:
            task_env = os.environ.copy()
            task_env['PYTHONUTF8'] = '1'
            process = launch([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                              '--port', str(args.port)], 'presentation-server.log', task_env)
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline and process.poll() is None:
                if get_status(client, base):
                    break
                time.sleep(.5)
        status = get_status(client, base)
        print(f'Open {base}')
        if status:
            print('Photo analysis:', status['services']['photo'])
            print('AI explanations:', status['services']['ollama'])
        if not status or status['status'] != 'ready':
            print('Check .env, installed model and presentation-server.log. Models are never downloaded automatically.')
            return 1
        print('Ready checks passed. Still verify one real generation and a PDF before the demo.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
