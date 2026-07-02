"""Agent template loader with {{VAR}} substitution."""

import json
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_templates() -> list[dict]:
    """Return all templates sorted by category then name."""
    templates = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            templates.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(
        templates,
        key=lambda t: (t.get("templateCategory", ""), t.get("templateName", "")),
    )


def get_template(template_id: str) -> dict | None:
    """Look up a single template by templateId."""
    for t in load_templates():
        if t.get("templateId") == template_id:
            return t
    return None


def render_template(template: dict, variables: dict[str, str]) -> dict:
    """
    Deep-substitute {{VAR}} placeholders in the agent subtree.
    Unrecognised placeholders are left unchanged.
    Returns the rendered `agent` dict.
    """
    raw = json.dumps(template.get("agent", {}))

    def replace(m: re.Match) -> str:
        return variables.get(m.group(1), m.group(0))

    return json.loads(re.sub(r"\{\{(\w+)\}\}", replace, raw))
