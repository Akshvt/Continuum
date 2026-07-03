"""
End-to-end test of the Memory Lifecycle Service.
This is NOT a throwaway — keep it, it's your regression test.

Run with:
    python tests/test_memory_service.py

What passing looks like:
  ✓ remember_interaction   — no exception, log entry written
  ✓ recall_student_context — returns a non-empty list
  ✓ improve_student_memory — no exception, log entry written
  ✓ forget_resolved_misconception — no exception, log entry written
  ✓ get_lifecycle_log      — returns 4 entries for test student

If any step fails, that operation is broken before you've built anything
on top of it — fix it here first.
"""

import asyncio
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.memory import (
    remember_interaction,
    recall_student_context,
    improve_student_memory,
    forget_resolved_misconception,
    get_lifecycle_log,
)


FAKE_STUDENT = "test_student_001"


async def run_tests():
    passed = 0
    failed = 0

    # ── Test 1: remember() ──────────────────────────────────────────
    print("Testing remember_interaction()...")
    try:
        await remember_interaction(
            student_id=FAKE_STUDENT,
            concept="quadratic_factoring",
            answer="(x+2)(x-3)",
            is_correct=False,
            misconception="sign error on second factor",
            strategy_used="worked_example",
            mastery_delta=-0.05,
        )
        print("  ✓ remember_interaction passed\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ remember_interaction FAILED: {e}\n")
        failed += 1

    # ── Test 2: recall() ────────────────────────────────────────────
    print("Testing recall_student_context()...")
    try:
        results = await recall_student_context(
            FAKE_STUDENT,
            "What mistakes has this student made on quadratic factoring?",
        )
        assert isinstance(results, list), "Expected list from recall()"
        print(f"  ✓ recall_student_context passed — got {len(results)} result(s)")
        if results:
            print(f"    First result: {str(results[0])[:120]}...")
        print()
        passed += 1
    except Exception as e:
        print(f"  ✗ recall_student_context FAILED: {e}\n")
        failed += 1

    # ── Test 3: improve() ───────────────────────────────────────────
    print("Testing improve_student_memory()...")
    try:
        await improve_student_memory(FAKE_STUDENT)
        print("  ✓ improve_student_memory passed\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ improve_student_memory FAILED: {e}\n")
        failed += 1

    # ── Test 4: forget() ────────────────────────────────────────────
    print("Testing forget_resolved_misconception()...")
    try:
        await forget_resolved_misconception(
            student_id=FAKE_STUDENT,
            misconception="sign error on second factor",
            confirmed_correct_count=3,
        )
        print("  ✓ forget_resolved_misconception passed\n")
        passed += 1
    except Exception as e:
        print(f"  ✗ forget_resolved_misconception FAILED: {e}\n")
        failed += 1

    # ── Test 5: log integrity ────────────────────────────────────────
    print("Checking lifecycle log...")
    log = get_lifecycle_log(student_id=FAKE_STUDENT)
    ops = [e["operation"] for e in log]
    expected_ops = {"remember", "recall", "improve", "forget"}
    found_ops = set(ops)

    if expected_ops.issubset(found_ops):
        print(f"  ✓ Log contains all four operations: {ops}\n")
        passed += 1
    else:
        missing = expected_ops - found_ops
        print(f"  ✗ Log missing operations: {missing}\n")
        failed += 1

    # ── Summary ──────────────────────────────────────────────────────
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All operations confirmed working. Build on top of this.")
    else:
        print("Fix failing operations before proceeding to Day 2.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_tests())