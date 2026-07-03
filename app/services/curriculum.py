"""Shared curriculum dataset for the tutoring engine."""

from __future__ import annotations

from pathlib import Path

from app.cognee_ops import recall, remember
from config import config


BASE_DIR = Path(__file__).resolve().parents[2]
CURRICULUM_MARKER = BASE_DIR / ".curriculum_seeded"
CURRICULUM_DATASET = config.CURRICULUM_DATASET


CURRICULUM_LADDER: list[dict[str, object]] = [
    {
        "concept": "literals_and_values",
        "prerequisites": [],
        "summary": "Students learn that Python values can be numbers, strings, and booleans.",
    },
    {
        "concept": "variables",
        "prerequisites": ["literals_and_values"],
        "summary": "Variables store values so later code can reuse them.",
    },
    {
        "concept": "data_types",
        "prerequisites": ["literals_and_values", "variables"],
        "summary": "Students distinguish integers, floats, strings, and booleans.",
    },
    {
        "concept": "print_and_input",
        "prerequisites": ["variables"],
        "summary": "Print shows output and input collects data from the user.",
    },
    {
        "concept": "operators",
        "prerequisites": ["variables", "data_types"],
        "summary": "Arithmetic operators combine values into new results.",
    },
    {
        "concept": "strings",
        "prerequisites": ["variables", "literals_and_values"],
        "summary": "Strings hold text and support indexing, slicing, and concatenation.",
    },
    {
        "concept": "boolean_logic",
        "prerequisites": ["operators", "data_types"],
        "summary": "Boolean expressions combine comparisons with and, or, and not.",
    },
    {
        "concept": "conditionals",
        "prerequisites": ["boolean_logic", "operators"],
        "summary": "If statements use boolean conditions to choose between paths.",
    },
    {
        "concept": "lists",
        "prerequisites": ["variables", "strings"],
        "summary": "Lists store ordered collections that students can index and iterate over.",
    },
    {
        "concept": "loops",
        "prerequisites": ["conditionals", "lists"],
        "summary": "For and while loops repeat work over collections or until a condition changes.",
    },
    {
        "concept": "functions",
        "prerequisites": ["variables", "conditionals"],
        "summary": "Functions package reusable logic with parameters and return values.",
    },
    {
        "concept": "dictionaries",
        "prerequisites": ["lists", "functions"],
        "summary": "Dictionaries map keys to values and are useful for structured data.",
    },
]

CURRICULUM_CONCEPTS = [entry["concept"] for entry in CURRICULUM_LADDER]
CURRICULUM_PREREQUISITES = {
    entry["concept"]: list(entry["prerequisites"])
    for entry in CURRICULUM_LADDER
}
CURRICULUM_SUMMARY = "\n".join(
    (
        f"{entry['concept']}: {entry['summary']} "
        f"Prerequisites: {', '.join(entry['prerequisites']) if entry['prerequisites'] else 'none'}."
    )
    for entry in CURRICULUM_LADDER
)


def normalize_concept_name(concept: str) -> str:
    return concept.strip().lower().replace(" ", "_").replace("-", "_")


def curriculum_prerequisites(concept: str) -> list[str]:
    return CURRICULUM_PREREQUISITES.get(normalize_concept_name(concept), [])


def curriculum_context() -> str:
    return CURRICULUM_SUMMARY


def curriculum_seeded() -> bool:
    return CURRICULUM_MARKER.exists()


async def seed_curriculum_dataset(force: bool = False) -> dict[str, object]:
    if curriculum_seeded() and not force:
        return {
            "status": "already_seeded",
            "dataset": CURRICULUM_DATASET,
            "concept_count": len(CURRICULUM_CONCEPTS),
        }

    try:
        for entry in CURRICULUM_LADDER:
            concept = entry["concept"]
            prerequisites = entry["prerequisites"]
            summary = entry["summary"]
            prerequisite_text = ", ".join(prerequisites) if prerequisites else "none"
            syllabus_line = (
                f"Concept {concept}. {summary} "
                f"This topic depends on {prerequisite_text}."
            )
            await remember(syllabus_line, dataset_name=CURRICULUM_DATASET)

        CURRICULUM_MARKER.write_text("seeded\n", encoding="utf-8")
        return {
            "status": "seeded",
            "dataset": CURRICULUM_DATASET,
            "concept_count": len(CURRICULUM_CONCEPTS),
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "dataset": CURRICULUM_DATASET,
            "concept_count": len(CURRICULUM_CONCEPTS),
            "error": str(exc),
        }


async def verify_curriculum_dataset() -> list:
    query = (
        "Which concepts depend on variables, conditionals, or lists? "
        "Explain the prerequisite relationships in the syllabus."
    )
    try:
        return await recall(query, datasets=[CURRICULUM_DATASET])
    except Exception:
        return []
