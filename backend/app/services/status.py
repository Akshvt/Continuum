import logging
from collections import defaultdict

logger = logging.getLogger("continuum.services.status")

pending_memory_writes: dict[str, int] = defaultdict(int)

def increment_pending(student_id: str) -> None:
    pending_memory_writes[student_id] += 1
    logger.info("Incremented pending memory writes for %s, total: %d", student_id, pending_memory_writes[student_id])

def decrement_pending(student_id: str) -> None:
    if pending_memory_writes[student_id] > 0:
        pending_memory_writes[student_id] -= 1
        logger.info("Decremented pending memory writes for %s, total: %d", student_id, pending_memory_writes[student_id])

def has_pending(student_id: str) -> bool:
    return pending_memory_writes[student_id] > 0
