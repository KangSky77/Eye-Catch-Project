"""Bounded HTTP load test against an already-running Eye-Catch server.

Uses repository demo photos and synthetic questionnaire facts. No patient data,
external clinic API, configuration changes, or model downloads. Results distinguish
HTTP success from stream errors and rule-based question fallbacks.
"""
import argparse
import asyncio
from collections import Counter
import ctypes
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("ko", "en", "ja", "zh", "es", "fr")
PHOTO_PATHS = ("static/assets/examples/face-good.jpg",
               "static/assets/diseases/cataract-clinical.jpg",
               "static/assets/examples/face-blurry.jpg")
PHOTOS = [(Path(p).name, (ROOT / p).read_bytes()) for p in PHOTO_PATHS]
# The browser limits the longest edge to 2000px. Upscale a CC0 demo image
# solely to exercise that computation size; this is not an accuracy dataset.
_large = io.BytesIO()
Image.open(ROOT / PHOTO_PATHS[0]).resize((2000, 1500)).save(_large, format="JPEG", quality=95)
LARGE_PHOTO = _large.getvalue()


def percentile(values, p):
    if not values:
        return None
    return round(sorted(values)[max(0, math.ceil(len(values) * p) - 1)], 3)


def stats(values):
    return {"p50_s": percentile(values, .5), "p95_s": percentile(values, .95),
            "max_s": round(max(values), 3) if values else None}


def opinion_payload(i):
    # Stable structured facts; no real participant information.
    return {"lang": LANGS[i % len(LANGS)], "cataract_res": "Photo screening: no obvious opacity",
            "amsler_res": "No distortion reported", "cataract_code": "normal",
            "chat_symptoms": ["Eye surgery: no", "Diabetes: no", "Hypertension: no"],
            "symptom_codes": [], "flag_codes": ["age_20s", "sym_chk_recent"],
            "triage_level": "monitor", "red_flags": []}


def question_payload(i):
    return {"lang": LANGS[i % len(LANGS)], "cataract_res": "Photo screening: no obvious opacity",
            "amsler_res": "No distortion reported", "cataract_code": "normal",
            "symptom_answers": {"cat_foggy": True}, "risk_answers": {"age": "20s"},
            "amsler_answers": {"left": False, "right": False},
            "chat_history": [{"q": "Do you experience foggy vision?", "a": "Yes"}],
            "asked_question_ids": [], "postoperative": False, "red_flags": []}


class MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong)]


def resources():
    if sys.platform != "win32":
        return {}
    m = MemoryStatus()
    m.length = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
    return {"ram_used_gib": round((m.total_phys - m.avail_phys) / 2**30, 3),
            "ram_available_gib": round(m.avail_phys / 2**30, 3),
            "cpu_idle": idle.value, "cpu_total": kernel.value + user.value}


def gpu_sample():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu,temperature.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3)
        vram, utilization, temperature = [int(v.strip()) for v in r.stdout.strip().split(",")]
        return {"gpu_vram_mib": vram, "gpu_util_percent": utilization, "gpu_temp_c": temperature}
    except Exception:
        return {}


class Runner:
    def __init__(self, args, client, assets):
        self.args, self.client, self.assets = args, client, assets
        self.rows, self.samples = [], []
        self.phase = "initial"
        self.session_client = ContextVar("load_test_visitor", default=None)

    async def request(self, kind, i=0, deadline=None):
        client = self.session_client.get() or self.client
        start = time.perf_counter()
        row = {"phase": self.phase, "kind": kind, "user": i, "ok": False}
        try:
            budget = deadline or (45 if kind == "question" and self.args.respect_browser_timeouts else self.args.deadline)
            async with asyncio.timeout(budget):
                if kind == "page":
                    response = await client.get("/")
                    response.raise_for_status()
                    if '<html' not in response.text.lower() or 'app-core.js' not in response.text:
                        raise ValueError("unexpected_html")
                    size = len(response.content)
                    assets = self.assets
                    if self.args.admission:
                        assets = sorted(set(re.findall(r'(?:src|href)="(/static/[^"?#]+(?:\?[^"#]*)?)"', response.text)))
                        assets.append("/static/vendor/pretendard/PretendardVariable.woff2")
                    slots = asyncio.Semaphore(6)
                    async def asset(path):
                        async with slots:
                            r = await client.get(path)
                            r.raise_for_status()
                            return len(r.content)
                    size += sum(await asyncio.gather(*(asset(p) for p in assets)))
                    status, extra = response.status_code, {"bytes": size}
                elif kind in ("photo", "largephoto"):
                    name, data = PHOTOS[i % len(PHOTOS)] if kind == "photo" else ("loadtest-2000.jpg", LARGE_PHOTO)
                    response = await client.post("/api/analyze-eye", files={"file": (name, data, "image/jpeg")})
                    response.raise_for_status()
                    result = response.json()
                    expected = ("normal", "risk", "blurry")[i % len(PHOTOS)] if kind == "photo" else "normal"
                    if result.get("status") != "success" or result.get("result_code") != expected:
                        raise ValueError("photo_result_changed:" + str(result.get("result_code")))
                    status, extra = response.status_code, {"result_code": result["result_code"]}
                elif kind == "question":
                    response = await client.post("/api/generate-next-question", json=question_payload(i))
                    response.raise_for_status()
                    result = response.json()
                    if not result.get("question") or result.get("done"):
                        raise ValueError("missing_question")
                    status, extra = response.status_code, {"source": result.get("source"),
                            "fallback_reason": result.get("fallback_reason"), "question_id": result.get("question_id")}
                elif kind == "status":
                    response = await client.get("/api/service-status")
                    response.raise_for_status()
                    if response.json().get("status") != "ready":
                        raise ValueError("service_not_ready")
                    status, extra = response.status_code, {}
                elif kind in ("opinion", "chat", "urgent"):
                    if kind == "chat":
                        path, payload = "/api/chat-with-gemma", {"lang": LANGS[i % len(LANGS)],
                            "user_msg": "What can I do when my eyes feel tired after looking at a screen?",
                            "context": "Synthetic demonstration, age in twenties, no surgery.", "facts": []}
                    else:
                        path, payload = "/api/get-ai-opinion", opinion_payload(i)
                        if kind == "urgent":
                            payload.update(red_flags=["rf_sudden_loss"], triage_level="urgent")
                    full, first_text, beats = "", None, 0
                    async with client.stream("POST", path, json=payload) as response:
                        response.raise_for_status()
                        header_s = time.perf_counter() - start
                        async for chunk in response.aiter_text():
                            beats += chunk.count("\u200b")
                            visible = chunk.replace("\u200b", "")
                            if visible.strip() and first_text is None:
                                first_text = time.perf_counter() - start
                            full += visible
                    if "__ECERR__" in full or not full.strip():
                        raise ValueError("stream_error:" + full[-150:])
                    status, extra = response.status_code, {"header_s": round(header_s, 3),
                        "first_text_s": round(first_text, 3) if first_text is not None else None,
                        "heartbeats": beats, "text_chars": len(full), "text_sha256": hashlib.sha256(full.encode()).hexdigest()}
                else:
                    response = await client.get("/healthz")
                    response.raise_for_status()
                    if response.json().get("status") != "ok":
                        raise ValueError("unhealthy")
                    status, extra = response.status_code, {}
                row.update(ok=True, status=status, **extra)
        except Exception as exc:
            row.update(error=type(exc).__name__ + ":" + str(exc)[:200])
        row["seconds"] = round(time.perf_counter() - start, 3)
        row["frontend_deadline_s"] = 45 if kind == "question" else 180
        row["within_frontend_deadline"] = row["ok"] and row["seconds"] < row["frontend_deadline_s"]
        self.rows.append(row)
        return row

    async def monitor(self, stop):
        previous, tick = None, 0
        while not stop.is_set():
            s = {"phase": self.phase, "time": datetime.now(timezone.utc).isoformat(), **resources()}
            if previous and s.get("cpu_total", 0) > previous.get("cpu_total", 0):
                s["cpu_percent"] = round(100 * (1 - (s["cpu_idle"] - previous["cpu_idle"]) /
                                                (s["cpu_total"] - previous["cpu_total"])), 1)
            previous = s
            if tick % 5 == 0:
                s.update(await asyncio.to_thread(gpu_sample))
            self.samples.append(s)
            await self.request("health", deadline=5)
            tick += 1
            try:
                await asyncio.wait_for(stop.wait(), 1)
            except TimeoutError:
                pass

    def summarize(self, phase, elapsed):
        rows = [r for r in self.rows if r["phase"] == phase]
        summary = {"phase": phase, "elapsed_s": round(elapsed, 3), "requests": {}}
        for kind in sorted({r["kind"] for r in rows}):
            group = [r for r in rows if r["kind"] == kind]
            summary["requests"][kind] = {"count": len(group), "success": sum(r["ok"] for r in group),
                "within_frontend_deadline": sum(r.get("within_frontend_deadline", r["ok"]) for r in group),
                **stats([r["seconds"] for r in group]),
                "errors": dict(Counter(r.get("error") for r in group if not r["ok"]))}
            if kind == "question":
                summary["requests"][kind]["sources"] = dict(Counter(r.get("source") for r in group if r["ok"]))
                summary["requests"][kind]["fallbacks"] = dict(Counter(r.get("fallback_reason") for r in group if r.get("fallback_reason")))
        return summary

    async def phase_run(self, specification):
        kind, n, waves = specification.split(":")
        n, waves = int(n), int(waves)
        self.phase = specification
        print("START", specification, flush=True)
        start = time.perf_counter()
        async def session(i):
            await self.request("page", i)
            await self.request("status", i, deadline=8)
            await self.request("photo", i)
            await asyncio.sleep(self.args.think)
            await self.request("question", i)
            await asyncio.sleep(self.args.think)
            await self.request("opinion", i)
        async def admitted_session(i):
            start_wait = time.perf_counter()
            row = {"phase": self.phase, "kind": "admission", "user": i, "ok": False}
            async with httpx.AsyncClient(base_url=self.args.url.rstrip("/"), headers=self.client.headers,
                                        trust_env=False, follow_redirects=True,
                                        timeout=httpx.Timeout(self.args.deadline, connect=10)) as visitor:
                context_token = self.session_client.set(visitor)
                try:
                    async with asyncio.timeout(600):
                        response = await visitor.post("/api/admission/join")
                        response.raise_for_status()
                        data = response.json()
                        row["initial_position"] = data["position"]
                        while data["enabled"] and data["state"] != "active":
                            await asyncio.sleep(data["poll_seconds"])
                            response = await visitor.get("/api/admission/status")
                            response.raise_for_status()
                            data = response.json()
                            if data["state"] == "idle":
                                raise ValueError("queue_ticket_expired")
                        row.update(ok=True, seconds=round(time.perf_counter() - start_wait, 3))
                    if kind == "mixed":
                        await session(i)
                    else:
                        await self.request(kind, i)
                except Exception as exc:
                    row.update(error=type(exc).__name__ + ":" + str(exc)[:200])
                finally:
                    row.setdefault("seconds", round(time.perf_counter() - start_wait, 3))
                    self.rows.append(row)
                    await visitor.post("/api/admission/leave")
                    self.session_client.reset(context_token)
        for wave in range(waves):
            if self.args.admission:
                await asyncio.gather(*(admitted_session(i + wave * n) for i in range(n)))
            elif kind == "mixed":
                await asyncio.gather(*(session(i + wave * n) for i in range(n)))
            elif kind == "overlap":
                await asyncio.gather(*(self.request(k, i + wave * n) for i in range(n)
                                       for k in ("photo", "opinion", "question")))
            else:
                await asyncio.gather(*(self.request(kind, i + wave * n) for i in range(n)))
            if waves > 1:
                print("WAVE", specification, wave + 1, "elapsed_s", round(time.perf_counter() - start, 1), flush=True)
        result = self.summarize(specification, time.perf_counter() - start)
        print(json.dumps(result, ensure_ascii=True), flush=True)
        return result


async def main(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "EyeCatch-BoundedLoadTest/1.0", "ngrok-skip-browser-warning": "1"}
    async with httpx.AsyncClient(base_url=args.url.rstrip("/"), headers=headers, trust_env=False,
                                timeout=httpx.Timeout(args.deadline, connect=10),
                                limits=httpx.Limits(max_connections=800, max_keepalive_connections=200)) as client:
        root = await client.get("/")
        root.raise_for_status()
        if 'data-waiting-entry' in root.text and not args.admission:
            raise SystemExit("Waiting room is enabled. Add --admission to test separate queued visitors.")
        assets = sorted(set(re.findall(r'(?:src|href)="(/static/[^"?#]+(?:\?[^"#]*)?)"', root.text)))
        assets.append("/static/vendor/pretendard/PretendardVariable.woff2")
        runner = Runner(args, client, assets)
        stop = asyncio.Event()
        monitor = asyncio.create_task(runner.monitor(stop))
        report = {"started_utc": datetime.now(timezone.utc).isoformat(), "base_url": args.url,
                  "deadline_s": args.deadline, "respect_browser_timeouts": args.respect_browser_timeouts,
                  "admission": args.admission,
                  "think_s": args.think, "languages": list(LANGS), "assets": assets,
                  "large_photo": {"size_px": [2000, 1500], "bytes": len(LARGE_PHOTO), "source": PHOTO_PATHS[0]},
                  "photo_files": [{"path": p, "sha256": hashlib.sha256(d).hexdigest(), "bytes": len(d)}
                                  for p, (_, d) in zip(PHOTO_PATHS, PHOTOS)], "phases": []}
        try:
            for phase in args.phase:
                report["phases"].append(await runner.phase_run(phase))
                (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                (out / "requests.json").write_text(json.dumps(runner.rows, ensure_ascii=False, indent=2), encoding="utf-8")
                (out / "resources.json").write_text(json.dumps(runner.samples, indent=2), encoding="utf-8")
        finally:
            stop.set()
            await monitor
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "requests.json").write_text(json.dumps(runner.rows, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "resources.json").write_text(json.dumps(runner.samples, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--phase", action="append", required=True, help="kind:concurrent_users:waves; page/photo/largephoto/opinion/question/chat/mixed/overlap/urgent")
    parser.add_argument("--output", required=True)
    parser.add_argument("--deadline", type=float, default=180, help="total per-request deadline including queue, matching frontend")
    parser.add_argument("--think", type=float, default=2)
    parser.add_argument("--respect-browser-timeouts", action="store_true", help="abort question requests after 45s, as the browser does")
    parser.add_argument("--admission", action="store_true", help="use separate visitor cookies, wait for admission, and release after each visit")
    parser.add_argument("--language", choices=("cycle", *LANGS), default="cycle")
    arguments = parser.parse_args()
    valid_kinds = {"page", "photo", "largephoto", "opinion", "question", "chat", "mixed", "overlap", "urgent"}
    for specification in arguments.phase:
        try:
            kind, count, waves = specification.split(":")
            if kind not in valid_kinds or not 1 <= int(count) <= 100 or not 1 <= int(waves) <= 20:
                raise ValueError
            if arguments.admission and kind == "overlap":
                parser.error("--admission requires sequential work per visitor; use mixed instead of overlap.")
        except ValueError:
            parser.error("Each phase must be kind:users:waves, with users=1..100 and waves=1..20.")
    if not 0 < arguments.deadline <= 600 or not 0 <= arguments.think <= 120:
        parser.error("deadline must be 0..600 seconds (exclusive zero); think must be 0..120 seconds.")
    if arguments.language != "cycle":
        LANGS = (arguments.language,)
    asyncio.run(main(arguments))
