"""
STEP 1 — Throwaway proof file.
Run this before writing any real application code.
If recall() returns something sensible → delete this file and start building.
If it errors → fix the config here before touching anything else.

Usage:
    python test_cognee.py
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()  # loads LLM_API_KEY from .env

import main as cognee_app


async def run_test():
    print("=== Cognee proof-of-life test ===\n")

    # 1. remember() — ingest one fake student interaction
    dataset = "proof_test"
    text = (
        "Student riya_001 attempted concept 'quadratic_factoring'. "
        "She answered (x+2)(x-3) but the correct answer was (x+2)(x+3). "
        "The misconception was a sign error on the second factor. "
        "Teaching strategy used was worked_example."
    )

    print("Calling remember()...")
    result = await cognee_app.remember(text, dataset_name=dataset)
    print(f"remember() result: {result}\n")

    # 2. recall() — query against what we just stored
    print("Calling recall()...")
    answers = await cognee_app.recall(
        "What mistake did riya_001 make on quadratic factoring?",
        datasets=[dataset],
    )

    print("recall() returned:")
    for item in answers:
        # Each item is a typed response object — print its dict representation
        print(f"  {item}\n")

    # 3. forget() — clean up test dataset so it doesn't pollute real data
    print("Calling forget() to clean up test dataset...")
    forget_result = await cognee_app.forget(dataset=dataset)
    print(f"forget() result: {forget_result}\n")

    print("=== All three operations worked. Delete this file and start building. ===")


if __name__ == "__main__":
    asyncio.run(run_test())