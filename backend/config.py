"""
Central config. Every other module imports from here.
Never read os.environ directly anywhere else in the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Force litellm to drop unsupported parameters (like dimensions for mistral-embed)
os.environ["LITELLM_DROP_PARAMS"] = "true"
if "EMBEDDING_DIMENSIONS" not in os.environ:
    os.environ["EMBEDDING_DIMENSIONS"] = "1024"

class Config:
    # App-level LLM config — used by grading.py and tutoring.py.
    # Uses APP_LLM_* prefix so it doesn't collide with Cognee's LLM_* vars.
    LLM_API_KEY: str = os.environ.get("APP_LLM_API_KEY", "")
    LLM_PROVIDER: str = os.environ.get("APP_LLM_PROVIDER", "mistral")
    LLM_MODEL: str = os.environ.get("APP_LLM_MODEL", "mistral-medium-latest")

    # Dataset naming convention: one per student, isolated from curriculum
    CURRICULUM_DATASET: str = "curriculum_global"

    # How many interactions before we auto-trigger improve()
    IMPROVE_TRIGGER_EVERY_N: int = 5

    # How many consecutive correct answers before we forget() a misconception
    FORGET_MISCONCEPTION_AFTER_N_CORRECT: int = 3

    def validate(self):
        if not self.LLM_API_KEY:
            print(
                "[startup] APP_LLM_API_KEY is not set; tutoring/grading LLM "
                "calls will use fallbacks."
            )

        # Warn about Cognee's own env vars — these are read directly by the
        # cognee package, not through this Config class
        cognee_vars = {
            "LLM_API_KEY": "Cognee LLM calls (remember/recall/improve/forget)",
            "EMBEDDING_API_KEY": "Cognee vector embeddings",
            "EMBEDDING_PROVIDER": "Cognee embedding provider selection",
        }
        for var, purpose in cognee_vars.items():
            if not os.environ.get(var):
                print(
                    f"[startup] {var} is not set; {purpose} will fail silently."
                )


config = Config()