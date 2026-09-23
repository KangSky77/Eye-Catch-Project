"""The photo body cap runs before Starlette's multipart file spooling."""

import asyncio

from app.core.upload_limit import PhotoUploadBodyLimit


def _run_upload(chunks, headers=(), max_file_bytes=4, envelope_bytes=2):
    received = []
    sent = []

    async def downstream(scope, receive, send):
        received.append(await receive())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    messages = [
        {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
        for i, chunk in enumerate(chunks)
    ]

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/api/analyze-eye", "headers": list(headers)}
    app = PhotoUploadBodyLimit(downstream, max_file_bytes, envelope_bytes)
    asyncio.run(app(scope, receive, send))
    return received, sent


def test_content_length_초과는_본문을_받기_전에_413():
    received, sent = _run_upload([b"tiny"], headers=[(b"content-length", b"100")])
    assert received == []
    assert sent[0]["status"] == 413


def test_chunked_upload_초과도_파서에_전달하지_않는다():
    received, sent = _run_upload([b"abc", b"defg"])
    assert received == []
    assert sent[0]["status"] == 413


def test_상한_이내의_본문은_그대로_전달한다():
    received, sent = _run_upload([b"abc", b"def"])
    assert received[0]["body"] == b"abc"
    assert sent[0]["status"] == 200
