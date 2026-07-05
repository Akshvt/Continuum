"""
Scale test to simulate 10 interactions via the LIVE API endpoints.
This triggers `improve()` twice (at 5 and 10).
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory import get_lifecycle_log, LOG_PATH  # noqa: E402


STUDENT_ID = "test_student_scale"
CONCEPT = "variables"
BASE_URL = "http://localhost:8001"  # Or local depending on where we test


async def main():
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx is required. Install with: pip install httpx")
        sys.exit(1)

    # Clear any previous lifecycle log for a clean run
    if LOG_PATH.exists():
        existing = json.loads(LOG_PATH.read_text())
        cleaned = [e for e in existing if e.get("student_id") != STUDENT_ID]
        LOG_PATH.write_text(json.dumps(cleaned, indent=2))
        print(f"[setup] Cleared previous events for student={STUDENT_ID}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Step 1: Generate a question
        print("\n" + "=" * 60)
        print("STEP 1: Generate initial tutoring question")
        print("=" * 60)

        payload_q = {
            "student_id": STUDENT_ID,
            "current_concept": CONCEPT
        }
        r_q = await client.post("/api/tutoring/question", json=payload_q)
        r_q.raise_for_status()
        q_data = r_q.json()
        question_text = q_data["question"]
        strategy = q_data["teaching_style"]

        # Step 2: Loop 10 answers
        for i in range(1, 11):
            print("\n" + "=" * 60)
            print(f"STEP 2.{i}: Submit Answer #{i}")
            print("=" * 60)

            payload_ans = {
                "student_id": STUDENT_ID,
                "concept": CONCEPT,
                "question": question_text,
                "student_answer": f"Answer {i}: Variables are boxes.",
                "strategy_used": strategy
            }

            t0 = time.time()
            resp = await client.post("/api/tutoring/answer", json=payload_ans)
            ans_time = time.time() - t0
            
            resp.raise_for_status()
            answer_data = resp.json()
            
            print(f"  API Response Time: {ans_time:.2f}s")
            print(f"  Triggers: {answer_data.get('triggers_fired', [])}")
            
            # Since background tasks handle remember/improve, we wait for them to finish in the log.
            # We want to measure how long the BACKGROUND task takes for `improve`.
            # But the HTTP API response time will always be fast.
            # Let's poll the log to measure actual background completion time.
            
            poll_start = time.time()
            found_events = 0
            
            for _ in range(15):
                log = get_lifecycle_log(STUDENT_ID)
                # Count remembers
                remembers = [e for e in log if e["operation"] == "remember"]
                improves = [e for e in log if e["operation"] == "improve"]
                
                if len(remembers) == i:
                    if i % 5 == 0:
                        if len(improves) == (i // 5):
                            bg_time = time.time() - poll_start
                            print(f"  -> Background task (improve) completed in {bg_time:.2f}s")
                            break
                    else:
                        bg_time = time.time() - poll_start
                        print(f"  -> Background task (remember) completed in {bg_time:.2f}s")
                        break
                
                await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
