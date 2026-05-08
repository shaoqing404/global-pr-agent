"""Global PR Agent demo package.

This package keeps the original code-side implementation lightweight while
adding a middle-platform friendly Agent workflow:
Information Search Report -> Human Confirmation -> PR Insight -> Draft ->
Specialist Review -> Human Revision -> Export.
"""

__all__ = [
    "schemas",
    "report_loader",
    "orchestrator",
    "reviewers",
    "exporter",
]
