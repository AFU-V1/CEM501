"""Construction message classifier used by every channel."""

CATEGORY_PRIORITY = {
    "URGENT": 0,
    "ACTION": 1,
    "FYI": 2,
    "ARCHIVE": 3,
}

MESSAGE_TYPE_KEYWORDS = (
    (
        "SAFETY",
        "URGENT",
        (
            "stop work", "lost time incident", "near miss", "first aid case",
            "safety", "incident", "injury", "unsafe", "hazard", "ppe",
        ),
    ),
    (
        "DELAY",
        "URGENT",
        (
            "notice of delay", "delay notice", "time extension",
            "liquidated damages", "critical path", "behind schedule",
            "extension of time", "slippage",
        ),
    ),
    (
        "RFI",
        "ACTION",
        (
            "rfi", "request for information", "clarification",
            "design discrepancy", "detail mismatch",
        ),
    ),
    (
        "APPROVAL",
        "ACTION",
        (
            "approval", "approve", "approved", "shop drawing",
            "submittal", "material approval", "sign off", "review and return",
        ),
    ),
    (
        "SITE_ISSUE",
        "ACTION",
        (
            "site issue", "field condition", "access issue", "utility conflict",
            "gas main", "water ingress", "congestion", "rework", "damage",
        ),
    ),
    (
        "PROCUREMENT",
        "ACTION",
        (
            "procurement", "purchase order", "lead time", "vendor",
            "delivery", "price adjustment", "material shortage",
            "supplier", "fabrication",
        ),
    ),
    (
        "REPORT",
        "FYI",
        (
            "daily report", "daily log", "weekly report", "weekly schedule",
            "progress update", "progress photo", "meeting minutes",
            "inspection report", "monitoring report", "test results",
        ),
    ),
)

JUNK_KEYWORDS = [
    "benefits", "offer", "digest", "fw:",
    "server maintenance", "system maintenance",
    "occupational health", "health checkup", "job application",
]


def classify_message(subject: str, sender: str, body: str = "") -> dict:
    """Return both workflow bucket and construction-specific message type."""
    del sender

    search_text = f"{subject} {body}".lower()

    for keyword in JUNK_KEYWORDS:
        if keyword in search_text:
            return {
                "category": "ARCHIVE",
                "message_type": "GENERAL",
                "matched_keyword": keyword,
                "priority": CATEGORY_PRIORITY["ARCHIVE"],
                "needs_reply": False,
            }

    for message_type, workflow_category, keywords in MESSAGE_TYPE_KEYWORDS:
        for keyword in keywords:
            if keyword in search_text:
                return {
                    "category": workflow_category,
                    "message_type": message_type,
                    "matched_keyword": keyword,
                    "priority": CATEGORY_PRIORITY[workflow_category],
                    "needs_reply": workflow_category in {"URGENT", "ACTION"},
                }

    single_groups = (
        ("URGENT", "SAFETY", ("urgent", "immediate", "claim", "complaint")),
        ("ACTION", "GENERAL", ("review", "deadline", "coordination", "permit")),
        ("FYI", "REPORT", ("update", "recap", "photos", "minutes", "progress", "log", "fyi")),
    )

    for workflow_category, message_type, keywords in single_groups:
        for keyword in keywords:
            if keyword in search_text:
                return {
                    "category": workflow_category,
                    "message_type": message_type,
                    "matched_keyword": keyword,
                    "priority": CATEGORY_PRIORITY[workflow_category],
                    "needs_reply": workflow_category in {"URGENT", "ACTION"},
                }

    return {
        "category": "ARCHIVE",
        "message_type": "GENERAL",
        "matched_keyword": "default",
        "priority": CATEGORY_PRIORITY["ARCHIVE"],
        "needs_reply": False,
    }


def triage_email(subject: str, sender: str, body: str = "") -> tuple[str, str]:
    """Backward-compatible wrapper for earlier milestone code."""
    result = classify_message(subject, sender, body)
    return result["category"], result["matched_keyword"]
