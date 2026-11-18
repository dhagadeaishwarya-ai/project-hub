import logging
from typing import List, Dict, Any

logger = logging.getLogger("projecthub.notifications")

# In-memory record of sent mock notifications
SENT: List[Dict[str, Any]] = []


def notify(to_email: str, subject: str, message: str) -> None:
    """Mock notification helper that records in-memory and emits a log line."""
    notification_record = {
        "to_email": to_email,
        "subject": subject,
        "message": message
    }
    SENT.append(notification_record)
    logger.info("MOCK NOTIFICATION to %s | Subject: %s | Content: %s", to_email, subject, message)


def clear_sent() -> None:
    """Clear all notifications recorded in memory (useful for test resets)."""
    SENT.clear()
