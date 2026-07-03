"""One-time seed script for the shared curriculum dataset."""

import asyncio

from dotenv import load_dotenv


load_dotenv()

from app.services.curriculum import seed_curriculum_dataset, verify_curriculum_dataset


async def main():
    seeded = await seed_curriculum_dataset()
    print("Seed result:")
    print(seeded)

    print("\nVerification recall:")
    verification = await verify_curriculum_dataset()
    for item in verification:
        print(item)


if __name__ == "__main__":
    asyncio.run(main())