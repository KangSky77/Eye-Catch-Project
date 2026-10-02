"""Read-only presentation readiness checks. No results are stored."""
import argparse
import asyncio
import sys
import httpx


async def check(base_url: str) -> int:
    failed = False
    async with httpx.AsyncClient(timeout=10.0) as client:
        for path in ("/healthz", "/readyz", "/api/service-status"):
            try:
                response = await client.get(base_url.rstrip("/") + path)
                print(path, response.status_code, response.json())
                failed |= response.status_code != 200
            except (httpx.HTTPError, ValueError) as exc:
                print(path, type(exc).__name__)
                failed = True
    print("Also verify one real photo analysis, AI generation and PDF on the presentation device.")
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    sys.exit(asyncio.run(check(args.url)))
