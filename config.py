"""
Central config. Every other module imports from here.
Never read os.environ directly anywhere else in the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    # Dataset naming convention: one per student, isolated from curriculum
    CURRICULUM_DATASET: str = "curriculum_global"

    # How many interactions before we auto-trigger improve()
    IMPROVE_TRIGGER_EVERY_N: int = 5

    # How many consecutive correct answers before we forget() a misconception
    FORGET_MISCONCEPTION_AFTER_N_CORRECT: int = 3

    def validate(self):
        if not self.LLM_API_KEY:
            print(
                "[startup] LLM_API_KEY is not set; starting in degraded mode."
            )


config = Config()