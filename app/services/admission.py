"""FIFO admission for the single-process presentation server; no screening data."""
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
import secrets
import threading
import time

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.services.service_faq import is_score_question

COOKIE = "ec_visit"


@dataclass
class Visitor:
    state: str
    seen: float
    jobs: int = 0
    retiring: bool = False


class Admission:
    def __init__(self, capacity=2, active_ttl=120, waiting_ttl=60, max_waiting=500,
                 enabled=True, clock=time.monotonic):
        self.capacity, self.active_ttl, self.waiting_ttl = capacity, active_ttl, waiting_ttl
        self.max_waiting, self.enabled, self.clock = max_waiting, enabled, clock
        self.visitors = OrderedDict()
        self.lock = threading.RLock()

    def _advance(self):
        now = self.clock()
        for token, v in list(self.visitors.items()):
            ttl = self.active_ttl if v.state == "active" else self.waiting_ttl
            if not v.jobs and (v.retiring or now - v.seen >= ttl):
                del self.visitors[token]
        free = self.capacity - sum(v.state == "active" for v in self.visitors.values())
        for v in self.visitors.values():
            if free <= 0:
                break
            if v.state == "waiting":
                v.state, v.seen = "active", now
                free -= 1

    def _status(self, token):
        v = self.visitors.get(token)
        waiting = [t for t, entry in self.visitors.items() if entry.state == "waiting"]
        return {"enabled": self.enabled, "state": ("finishing" if v.retiring else v.state) if v else "idle",
                "position": waiting.index(token) + 1 if token in waiting else 0,
                "active": sum(entry.state == "active" for entry in self.visitors.values()),
                "capacity": self.capacity, "poll_seconds": 5,
                "explanation_requires_seat": settings.explain_mode != "fixed"}

    def join(self, token):
        with self.lock:
            self._advance()
            if not self.enabled:
                return token, {**self._status(token), "state": "active"}
            if token not in self.visitors:
                if sum(v.state == "waiting" for v in self.visitors.values()) >= self.max_waiting:
                    raise HTTPException(503, detail={"code": "WAITING_ROOM_FULL"}, headers={"Retry-After": "10"})
                token = secrets.token_urlsafe(32)
                self.visitors[token] = Visitor("waiting", self.clock())
            elif self.visitors[token].retiring:
                raise HTTPException(409, detail={"code": "VISIT_FINISHING"}, headers={"Retry-After": "5"})
            self.visitors[token].seen = self.clock()
            self._advance()
            return token, self._status(token)

    def status(self, token, renew=True):
        with self.lock:
            self._advance()
            if renew and token in self.visitors and not self.visitors[token].retiring:
                self.visitors[token].seen = self.clock()
            return self._status(token)

    def release(self, token):
        with self.lock:
            if token in self.visitors:
                self.visitors[token].retiring = True
            self._advance()
            return self._status(None)

    @contextmanager
    def job(self, token):
        if not self.enabled:
            yield
            return
        with self.lock:
            self._advance()
            visitor = self.visitors.get(token)
            if not visitor or visitor.state != "active" or visitor.retiring:
                raise HTTPException(429, detail={"code": "ADMISSION_REQUIRED"}, headers={"Retry-After": "5"})
            if visitor.jobs:
                raise HTTPException(409, detail={"code": "VISITOR_BUSY"}, headers={"Retry-After": "2"})
            visitor.jobs += 1
            visitor.seen = self.clock()
        try:
            yield
        finally:
            with self.lock:
                visitor.jobs -= 1
                # A long generation is activity, even if a phone timer was paused.
                visitor.seen = self.clock()
                self._advance()


async def require_admission(request: Request):
    """Yield dependency stays pinned until streaming responses finish/cancel."""
    store = request.app.state.admission
    if not store.enabled or getattr(request.state, "admission_pinned", False):
        yield
        return
    if request.url.path in {"/api/get-ai-opinion", "/api/chat-with-gemma"}:
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
        if (request.url.path == "/api/get-ai-opinion"
                and (data.get("red_flags") or data.get("triage_level") == "urgent")):
            yield
            return
        if (request.url.path == "/api/chat-with-gemma" and data.get("explain_results") is True
                and settings.explain_mode == "fixed"):
            yield
            return
        if (request.url.path == "/api/chat-with-gemma" and data.get("explain_results") is not True
                and isinstance(data.get("user_msg"), str) and is_score_question(data["user_msg"])):
            yield
            return
    with store.job(request.cookies.get(COOKIE)):
        yield


class AdmissionUploadGate:
    """Reject non-admitted uploads before buffering or parsing multipart."""
    def __init__(self, app, store):
        self.app, self.store = app, store

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/analyze-eye" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        try:
            with self.store.job(request.cookies.get(COOKIE)):
                scope.setdefault("state", {})["admission_pinned"] = True
                await self.app(scope, receive, send)
        except HTTPException as exc:
            await JSONResponse({"detail": exc.detail}, status_code=exc.status_code,
                               headers=exc.headers)(scope, receive, send)
