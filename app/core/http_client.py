"""TLS configuration shared by the local/VPN AI worker clients.

On Windows rebuilding the default certificate context for every short worker
request blocks the event loop. Reusing this context preserves HTTPX's default
certificate and hostname checks while keeping clients' lifetimes unchanged.
"""
from functools import lru_cache
import ssl

import httpx


@lru_cache(maxsize=1)
def worker_ssl_context() -> ssl.SSLContext:
    return httpx.create_ssl_context(verify=True, trust_env=True)
