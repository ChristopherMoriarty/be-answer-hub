API_PREFIX = "/api/v1"

STEP_KIND_LABELS: dict[str, str] = {
    "applied": "Applied",
    "hr_screen": "Screening",
    "technical": "Technical interview",
    "live_coding": "Live coding",
    "system_design": "System design",
    "culture_fit": "Culture fit",
    "final": "Final round",
    "custom": "Custom",
}

ALLOWED_STEP_KINDS = frozenset(STEP_KIND_LABELS)

DEFAULT_BOARD_COLUMN_KINDS: tuple[str, ...] = ("applied", "hr_screen", "technical")

ALLOWED_RESULTS = frozenset(
    {"in_progress", "rejected", "withdrawn", "ghosted", "on_hold", "offer"}
)

ALLOWED_STEP_STATUSES = frozenset(
    {"empty", "scheduled", "passed", "failed", "skipped", "cancelled"}
)

RESULT_LABELS: dict[str, str] = {
    "in_progress": "In progress",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
    "ghosted": "Ghosted",
    "on_hold": "On hold",
    "offer": "Offer",
}
