import json
from pathlib import Path

# Load rules once at startup
_rules_path = Path("rules.json")
_rules: list[dict] = json.loads(_rules_path.read_text())


def match_reply(message: str) -> str | None:
    """
    Checks the incoming message against every rule in rules.json.
    Returns the reply string for the FIRST matching rule, or None.
    Matching is case-insensitive; any keyword present in the message triggers the rule.
    """
    lower = message.lower()

    for rule in _rules:
        if any(kw.lower() in lower for kw in rule["keywords"]):
            return rule["reply"]

    return None
