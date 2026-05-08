"""
classifier.py -- Classifier component
Takes an email and classifies it by urgency using keyword triage.
"""

CATEGORY_PRIORITY = {
    "URGENT": 0,
    "ACTION": 1,
    "FYI": 2,
    "ARCHIVE": 3,
}

def triage_email(subject: str, sender: str, body: str = "") -> tuple[str, str]:
    del sender

    search_text = f"{subject} {body}".lower()

    # Pass 0: check obvious junk/non-project words immediately
    junk_keywords = [
        "benefits", "offer", "digest", "fw:",
        "server maintenance", "system maintenance",
        "occupational health", "health checkup", "job application",
    ]
    for keyword in junk_keywords:
        if keyword in search_text:
            return "ARCHIVE", keyword

    # Pass 1: compound (multi-word) keywords checked first for specificity.
    compound_groups = (
        ("URGENT", (
            "stop work", "notice of delay", "time extension",
            "liquidated damages", "vibration damage",
        )),
        ("ACTION", (
            "change order", "response required", "action required",
            "meeting request", "shop drawing", "permit renewal",
            "price adjustment", "renewal required",
            "certificate of insurance", "installation schedule",
            "gas main",
        )),
        ("FYI", (
            "meeting minutes", "daily log", "work log", "daily report",
            "progress photo", "test results", "weekly schedule",
            "weekly report", "schedule update",
            "safety inspection", "safety report", "inspection report",
            "monitoring report", "noise monitoring",
            "survey completed", "as-built",
            "no incidents", "no issues",
        )),
    )

    for category, keywords in compound_groups:
        for keyword in keywords:
            if keyword in search_text:
                return category, keyword

    # Pass 2: single-word keywords for broader matching.
    single_groups = (
        ("URGENT", (
            "urgent", "safety", "incident", "notice", "claim", "immediate",
            "complaint", "damage",
        )),
        ("ACTION", (
            "rfi", "submittal", "review", "approval", "deadline",
            "coordination", "permit", "insurance", "renewal",
        )),
        ("FYI", (
            "update", "recap", "photos", "minutes", "progress", "log", "fyi",
            "monitoring", "completed",
        )),
    )

    for category, keywords in single_groups:
        for keyword in keywords:
            if keyword in search_text:
                return category, keyword

    return "ARCHIVE", "default"
