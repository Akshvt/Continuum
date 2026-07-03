"""
Standalone diagnostic for the data_id: null bug — final version.

Differences from earlier runs:
  - Loads .env so LLM_API_KEY is available (same as uvicorn does)
  - Calls raw cognee.remember() directly so no exception is swallowed
  - Dumps RememberResult fully, including raw_result / cognify_result shape

Run with:
    cd backend
    python -X utf8 diagnose_remember.py
"""
import asyncio
import sys
import os
import traceback
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]

# Must be first: load .env BEFORE importing cognee or config so the
# LLM keys are in the environment — exactly as uvicorn does via config.py.
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from app.cognee_patches import apply_patches
apply_patches()

from cognee import remember as _raw_remember


async def main():
    text = (
        "Student diag_test_v3 attempted concept variables. "
        "Answer was incorrect. Strategy used: question_first. "
        "Mastery delta: -0.15. "
        "Misconception: confuses variable with literal."
    )
    dataset = "student_diag_test_v3"

    print("=" * 65)
    print("Calling raw cognee.remember() with .env loaded...")
    print(f"  LLM_API_KEY set: {bool(os.environ.get('LLM_API_KEY') or os.environ.get('MISTRAL_API_KEY'))}")
    print(f"  LLM_MODEL: {os.environ.get('LLM_MODEL', 'not set')}")
    print(f"  ENABLE_BACKEND_ACCESS_CONTROL: {os.environ.get('ENABLE_BACKEND_ACCESS_CONTROL', 'not set')}")
    print("=" * 65)

    result = None
    exc_info = None
    try:
        result = await _raw_remember(text, dataset_name=dataset)
    except Exception as exc:
        exc_info = (type(exc).__name__, str(exc), traceback.format_exc())

    print("\nRememberResult fields after return:")

    if exc_info is not None:
        print(f"\n  [EXCEPTION] remember() raised an exception:")
        print(f"  Type: {exc_info[0]}")
        print(f"  Message: {exc_info[1]}")
        print(f"\n  Full traceback:")
        print(exc_info[2])
        return

    if result is None:
        print("  result is None — returned None without raising.")
        return

    print(f"  result type:            {type(result).__name__}")
    print(f"  result.status:          {result.status!r}")
    print(f"  result.dataset_name:    {result.dataset_name!r}")
    print(f"  result.dataset_id:      {result.dataset_id!r}")
    print(f"  result.pipeline_run_id: {result.pipeline_run_id!r}")
    print(f"  result.items_processed: {result.items_processed!r}")
    print(f"  result.items:           {result.items!r}")
    print(f"  result.entry_id:        {result.entry_id!r}")
    print(f"  result.entry_type:      {result.entry_type!r}")
    print(f"  result.content_hash:    {result.content_hash!r}")
    print(f"  result.error:           {result.error!r}")
    print(f"  result.elapsed_seconds: {result.elapsed_seconds!r}")

    print()
    print("-" * 65)
    print("raw_result (= cognify_result passed into _resolve()):")
    raw = result.raw_result
    print(f"  type:    {type(raw).__name__}")
    print(f"  is None: {raw is None}")
    print(f"  bool():  {bool(raw) if raw is not None else 'N/A'}")
    print(f"  repr:    {raw!r}")

    if isinstance(raw, dict):
        print(f"\n  raw_result is a dict with {len(raw)} key(s):")
        for k, v in raw.items():
            print(f"\n    key={k!r}  (type={type(k).__name__})")
            print(f"    val type:   {type(v).__name__}")
            print(f"    val repr:   {v!r}")
            for attr in ("status", "pipeline_run_id", "payload",
                         "data_ingestion_info", "task_status", "error"):
                val = getattr(v, attr, "<<missing>>")
                print(f"    .{attr}: {val!r}")
        if len(raw) == 0:
            print("  [EMPTY DICT] — _resolve() hits early-exit, items stays []")
    else:
        print(f"\n  raw_result is NOT a dict.")
        print(f"  _resolve() early-exit path -> .items stays [].")

    print()
    print("=" * 65)
    print("datasets.list_data for the dataset:")
    try:
        import cognee
        from cognee.modules.users.methods import get_default_user
        from cognee.modules.engine.operations.setup import setup
        await setup()
        user = await get_default_user()
        # Find the dataset we just wrote to
        all_ds = await cognee.datasets.list_datasets(user=user)
        print(f"  All datasets: {[str(d.name) for d in all_ds]}")
        target = next((d for d in all_ds if d.name == dataset), None)
        if target:
            data_records = await cognee.datasets.list_data(target.id, user=user)
            print(f"  Data records in '{dataset}': {data_records!r}")
        else:
            print(f"  Dataset '{dataset}' not found in list.")
    except Exception as e:
        print(f"  datasets.list_data failed: {type(e).__name__}: {e}")

    print()
    items = getattr(result, "items", None)
    data_id = None
    if items and isinstance(items, list) and len(items) > 0:
        first_item = items[0]
        if isinstance(first_item, dict) and "id" in first_item:
            data_id = str(first_item["id"])
    print(f"  extracted data_id from result.items: {data_id!r}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
