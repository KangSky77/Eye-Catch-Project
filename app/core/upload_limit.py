"""Bound photo request bodies before Starlette parses multipart file parts."""

from starlette.responses import JSONResponse


class PhotoUploadBodyLimit:
    """Reject oversized photo requests before UploadFile can spool them to disk.

    The multipart envelope needs a little room beyond the image limit. The file
    itself is still checked separately by validate_and_read_image().
    """

    def __init__(self, app, max_file_bytes: int, envelope_bytes: int = 64 * 1024):
        self.app = app
        self.max_body_bytes = max_file_bytes + envelope_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") != "POST" or scope.get("path") != "/api/analyze-eye":
            await self.app(scope, receive, send)
            return

        async def reject():
            response = JSONResponse(
                status_code=413,
                content={"detail": {"code": "IMAGE_FILE_SIZE", "message": "사진 요청의 크기 제한을 초과했습니다."}},
            )
            await response(scope, receive, send)

        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    if int(value) > self.max_body_bytes:
                        await reject()
                        return
                except ValueError:
                    pass

        # Buffer only this bounded request before handing it to the multipart
        # parser. This also covers chunked requests without Content-Length.
        messages = []
        total = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                messages.append(message)
                continue
            total += len(message.get("body", b""))
            if total > self.max_body_bytes:
                await reject()
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        cursor = 0

        async def replay():
            nonlocal cursor
            if cursor < len(messages):
                message = messages[cursor]
                cursor += 1
                return message
            return await receive()

        await self.app(scope, replay, send)
