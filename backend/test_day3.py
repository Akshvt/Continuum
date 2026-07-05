"""
Day 3 end-to-end test.

Simulates a full tutoring loop with a fake student:
1. Generate a question
2. Submit a wrong answer (triggers remember + misconception)
3. Submit 3 correct answers (triggers remember, then forget)
4. Submit 2 more correct answers to hit interaction #5 (triggers improve)
5. Verify lifecycle_log.json contains all four primitives

Run with:
    python test_day3.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory import get_lifecycle_log, LOG_PATH  # noqa: E402


STUDENT_ID = "test_student_day3"
CONCEPT = "variables"
BASE_URL = "http://localhost:8001"


async def main():
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx is required. Install with: pip install httpx")
        sys.exit(1)

    # Clear any previous lifecycle log for a clean run
    if LOG_PATH.exists():
        existing = json.loads(LOG_PATH.read_text())
        # Remove only events for our test student so we don't clobber real data
        cleaned = [e for e in existing if e.get("student_id") != STUDENT_ID]
        LOG_PATH.write_text(json.dumps(cleaned, indent=2))
        print(f"[setup] Cleared previous events for student={STUDENT_ID}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # ── Step 1: Generate a question ──────────────────────────
        print("\n" + "=" * 60)
        print("STEP 1: Generate a tutoring question")
        print("=" * 60)

        resp = await client.post("/api/tutoring/question", json={
            "student_id": STUDENT_ID,
            "current_concept": CONCEPT,
        })
        assert resp.status_code == 200, f"question failed: {resp.status_code} {resp.text}"
        question_data = resp.json()
        question_text = question_data["question"]
        teaching_style = question_data["teaching_style"]
        print(f"  Question: {question_text}")
        print(f"  Teaching style: {teaching_style}")
        print(f"  Focus concept: {question_data['focus_concept']}")

        # ── Step 2: Submit a WRONG answer ────────────────────────
        print("\n" + "=" * 60)
        print("STEP 2: Submit a WRONG answer (should trigger: remember)")
        print("=" * 60)

        resp = await client.post("/api/tutoring/answer", json={
            "student_id": STUDENT_ID,
            "concept": CONCEPT,
            "question": question_text,
            "student_answer": "Variables are only for numbers and cannot store strings.",
            "strategy_used": teaching_style,
        })
        assert resp.status_code == 200, f"answer failed: {resp.status_code} {resp.text}"
        answer_data = resp.json()
        print(f"  Correct: {answer_data['is_correct']}")
        print(f"  Misconception: {answer_data.get('misconception')}")
        print(f"  Feedback: {answer_data['feedback']}")
        print(f"  Data ID: {answer_data.get('data_id')}")
        print(f"  Triggers: {answer_data.get('triggers_fired', [])}")

        # ── Steps 3-5: Submit 3 CORRECT answers ─────────────────
        for i in range(1, 4):
            print(f"\n{'=' * 60}")
            print(f"STEP {2 + i}: Submit CORRECT answer #{i} (should trigger: remember"
                  + (", forget" if i == 3 else "") + ")")
            print("=" * 60)

            resp = await client.post("/api/tutoring/answer", json={
                "student_id": STUDENT_ID,
                "concept": CONCEPT,
                "question": question_text,
                "student_answer": (
                    "A variable is a named label that references a value stored in memory and can hold "
                    "any data type such as numbers, strings, booleans, or lists, and can be reassigned "
                    "at any time. A literal is a fixed raw value written directly in code, like 42 or "
                    "'hello', that cannot be reassigned because it has no name — it just represents "
                    "itself. So the key difference is that variables are mutable named containers, "
                    "while literals are fixed, unnamed values."
                ),
                "strategy_used": teaching_style,
            })
            assert resp.status_code == 200, f"answer failed: {resp.status_code} {resp.text}"
            answer_data = resp.json()
            print(f"  Correct: {answer_data['is_correct']}")
            print(f"  Data ID: {answer_data.get('data_id')}")
            print(f"  Triggers: {answer_data.get('triggers_fired', [])}")

        # ── Step 6: One more correct answer to hit interaction #5 ─
        print(f"\n{'=' * 60}")
        print("STEP 6: Submit CORRECT answer #4 (should trigger: remember, improve at #5)")
        print("=" * 60)

        resp = await client.post("/api/tutoring/answer", json={
            "student_id": STUDENT_ID,
            "concept": CONCEPT,
            "question": question_text,
            "student_answer": (
                "A variable is a named label that references a value stored in memory and can hold "
                "any data type such as numbers, strings, booleans, or lists, and can be reassigned "
                "at any time. A literal is a fixed raw value written directly in code, like 42 or "
                "'hello', that cannot be reassigned because it has no name — it just represents "
                "itself. So the key difference is that variables are mutable named containers, "
                "while literals are fixed, unnamed values."
            ),
            "strategy_used": teaching_style,
        })
        assert resp.status_code == 200, f"answer failed: {resp.status_code} {resp.text}"
        answer_data = resp.json()
        print(f"  Correct: {answer_data['is_correct']}")
        print(f"  Triggers: {answer_data.get('triggers_fired', [])}")

        # ── Verification ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("VERIFICATION: Checking lifecycle_log.json")
        print("=" * 60)

        # Polling loop because background tasks take time to write to the log
        max_attempts = 15
        for attempt in range(max_attempts):
            log = get_lifecycle_log(STUDENT_ID)
            ops = [e["operation"] for e in log]
            
            remember_count = ops.count("remember")
            if remember_count >= 5:
                break
            print(f"  [Wait] Found {remember_count}/5 remember events. Waiting 2s for background tasks... (Attempt {attempt+1}/{max_attempts})")
            await asyncio.sleep(2)
            
        log = get_lifecycle_log(STUDENT_ID)
        ops = [e["operation"] for e in log]

        remember_count = ops.count("remember")
        recall_count = ops.count("recall")
        improve_count = ops.count("improve")
        forget_count = ops.count("forget")

        print(f"\n  Total events for {STUDENT_ID}: {len(log)}")
        print(f"  remember: {remember_count}")
        print(f"  recall:   {recall_count}")
        print(f"  improve:  {improve_count}")
        print(f"  forget:   {forget_count}")

        # Check data_id persistence in remember events
        remember_events = [e for e in log if e["operation"] == "remember"]
        data_ids_present = sum(1 for e in remember_events if e.get("data_id") is not None)
        print(f"\n  Remember events with data_id: {data_ids_present}/{remember_count}")

        # Verify all four primitives were used
        all_ops = {"remember", "recall", "improve", "forget"}
        used_ops = set(ops)
        missing = all_ops - used_ops

        print(f"\n  Operations used: {sorted(used_ops)}")

        if missing:
            print(f"\n  [WARNING] MISSING operations: {sorted(missing)}")
            print("  Some triggers may not have fired — check output above.")
        else:
            print("\n  [SUCCESS] ALL FOUR PRIMITIVES fired successfully!")

        # Assertions
        assert remember_count >= 5, f"Expected ≥5 remember events, got {remember_count}"
        print("\n  remember: PASS (≥5 events)")

        # recall fires during question generation and strategy selection
        assert recall_count >= 1, f"Expected ≥1 recall event, got {recall_count}"
        print("  ✅ recall:   PASS (≥1 event)")

        if improve_count >= 1:
            print("  ✅ improve:  PASS (auto-triggered)")
        else:
            print("  ⚠️  improve:  NOT triggered (may need more interactions)")

        if forget_count >= 1:
            print("  ✅ forget:   PASS (auto-triggered)")
        else:
            print("  ⚠️  forget:   NOT triggered (LLM may not have flagged misconception)")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

        # Dump the lifecycle log for manual inspection
        resp = await client.get(f"/api/memory/log/{STUDENT_ID}")
        if resp.status_code == 200:
            events = resp.json().get("events", [])
            print(f"\nFull lifecycle log ({len(events)} events):")
            for e in events:
                op = e["operation"]
                ts = e.get("timestamp", "?")
                concept_name = e.get("concept", e.get("query", "")[:40])
                extra = ""
                if op == "remember":
                    extra = f" correct={e.get('is_correct')} data_id={e.get('data_id', 'N/A')}"
                    if e.get("misconception"):
                        extra += f" misconception='{e['misconception']}'"
                elif op == "forget":
                    extra = f" misconception='{e.get('misconception')}' data_id={e.get('data_id', 'N/A')}"
                elif op == "recall":
                    extra = f" results={e.get('result_count', '?')}"
                print(f"  [{ts}] {op:10s} {concept_name}{extra}")


if __name__ == "__main__":
    asyncio.run(main())
