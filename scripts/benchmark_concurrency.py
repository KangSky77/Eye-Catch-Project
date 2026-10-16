"""
Real-world concurrency & load benchmark for Eye-Catch presentation server.
Simulates realistic end-to-end user journeys:
  1. Join admission (or wait in queue)
  2. Upload & analyze eye photo (Vision AI: MTCNN + EfficientNet)
  3. Search nearby eye clinics (Kakao Map API)
  4. Stream AI 3-line clinical summary (Ollama Gemma LLM)
  5. Leave admission
"""
import asyncio
import io
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = ROOT / "tests" / "generated_test_photos" / "01_normal_face.jpg"
BASE_URL = "http://127.0.0.1:8001"

async def simulate_user(user_id: int, image_bytes: bytes, timeout_sec: float = 90.0) -> dict:
    t_start = time.perf_counter()
    metrics = {
        "user_id": user_id,
        "success": False,
        "wait_in_queue_sec": 0.0,
        "vision_latency_sec": 0.0,
        "map_latency_sec": 0.0,
        "llm_latency_sec": 0.0,
        "total_latency_sec": 0.0,
        "error": None
    }
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=timeout_sec) as client:
        try:
            # Step 1: Join admission
            t0 = time.perf_counter()
            res_join = await client.post("/api/admission/join")
            res_join.raise_for_status()
            join_data = res_join.json()
            
            # If waiting in queue, poll like real frontend
            queue_start = time.perf_counter()
            while join_data.get("state") == "waiting":
                await asyncio.sleep(2.0)
                res_status = await client.get("/api/admission/status")
                res_status.raise_for_status()
                join_data = res_status.json()
                if time.perf_counter() - queue_start > timeout_sec:
                    raise TimeoutError("Queue wait timeout exceeded")
            metrics["wait_in_queue_sec"] = time.perf_counter() - queue_start

            # Step 2: Upload and analyze eye photo
            t_vision = time.perf_counter()
            files = {"file": ("face.jpg", io.BytesIO(image_bytes), "image/jpeg")}
            res_vision = await client.post("/api/analyze-eye", files=files)
            if res_vision.status_code != 200:
                raise RuntimeError(f"Vision failed with {res_vision.status_code}: {res_vision.text[:100]}")
            vision_data = res_vision.json()
            metrics["vision_latency_sec"] = time.perf_counter() - t_vision

            # Step 3: Search nearby clinics
            t_map = time.perf_counter()
            res_map = await client.get("/api/nearby-clinics?lat=37.5665&lng=126.9780")
            if res_map.status_code == 200:
                metrics["map_latency_sec"] = time.perf_counter() - t_map

            # Step 4: Stream AI opinion from Gemma (Ollama)
            t_llm = time.perf_counter()
            payload = {
                "cataract_res": vision_data.get("result", ""),
                "cataract_code": vision_data.get("result_code", "normal"),
                "amsler_res": "정상",
                "amsler_abnormal": False,
                "chat_symptoms": ["증상 없음"],
                "symptom_codes": [],
                "lang": "ko",
                "eye_asymmetric": vision_data.get("asymmetric", False),
                "red_flags": [],
                "triage_level": "monitor",
                "flag_codes": []
            }
            res_opinion = await client.post("/api/get-ai-opinion", json=payload)
            if res_opinion.status_code != 200:
                raise RuntimeError(f"Opinion failed with {res_opinion.status_code}: {res_opinion.text[:100]}")
            opinion_text = res_opinion.text
            metrics["llm_latency_sec"] = time.perf_counter() - t_llm

            # Step 5: Leave
            await client.post("/api/admission/leave")
            
            metrics["success"] = True
            metrics["total_latency_sec"] = time.perf_counter() - t_start
        except Exception as exc:
            metrics["error"] = f"{type(exc).__name__}: {str(exc)[:100]}"
            metrics["total_latency_sec"] = time.perf_counter() - t_start
            # Try to release seat
            try:
                await client.post("/api/admission/leave")
            except Exception:
                pass
                
    return metrics

async def run_scenario(concurrency: int, image_bytes: bytes) -> list[dict]:
    print(f"\n" + "=" * 70)
    print(f"🚀 Running benchmark with {concurrency} concurrent simulated user(s)...")
    print("=" * 70)
    
    t_start = time.perf_counter()
    tasks = [simulate_user(i + 1, image_bytes) for i in range(concurrency)]
    results = await asyncio.gather(*tasks)
    t_total = time.perf_counter() - t_start
    
    success_count = sum(1 for r in results if r["success"])
    print(f"Done in {t_total:.2f}s! ({success_count}/{concurrency} succeeded)")
    print(f"{'User':<6} | {'Status':<7} | {'Queue Wait':<10} | {'Vision AI':<10} | {'LLM Gen':<10} | {'Total Time':<10} | {'Notes'}")
    print("-" * 75)
    for r in results:
        status_str = "SUCCESS" if r["success"] else "FAIL"
        note = r["error"] if r["error"] else "OK"
        print(f"U{r['user_id']:<4} | {status_str:<7} | {r['wait_in_queue_sec']:<8.2f}s | {r['vision_latency_sec']:<8.2f}s | {r['llm_latency_sec']:<8.2f}s | {r['total_latency_sec']:<8.2f}s | {note}")
    
    if success_count > 0:
        succ_results = [r for r in results if r["success"]]
        avg_vision = sum(r["vision_latency_sec"] for r in succ_results) / len(succ_results)
        avg_llm = sum(r["llm_latency_sec"] for r in succ_results) / len(succ_results)
        avg_total = sum(r["total_latency_sec"] for r in succ_results) / len(succ_results)
        print(f"\nAverage among successful users:")
        print(f"  - Vision AI: {avg_vision:.2f}s")
        print(f"  - LLM Gen:   {avg_llm:.2f}s")
        print(f"  - Total E2E: {avg_total:.2f}s")
    
    return results

async def main():
    if not IMAGE_PATH.exists():
        print(f"Error: Test image not found at {IMAGE_PATH}")
        return
        
    image_bytes = IMAGE_PATH.read_bytes()
    
    # 1 User Baseline
    await run_scenario(1, image_bytes)
    await asyncio.sleep(2.0)
    
    # 2 Users Concurrency (Config capacity = 2)
    await run_scenario(2, image_bytes)
    await asyncio.sleep(2.0)
    
    # 4 Users Concurrency (Queue test: 2 active, 2 queued)
    await run_scenario(4, image_bytes)

if __name__ == "__main__":
    asyncio.run(main())
