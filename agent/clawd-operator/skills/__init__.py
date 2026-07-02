#!/usr/bin/env python3
# ABOUTME: Skill registry for Clawdbot Operator
# ABOUTME: Discovers, loads, and indexes all SKILL.md files for prompt injection

"""Skill registry for the OpenClawd Operator.

Discovers all ``SKILL.md`` files under ``skills/``, parses their YAML frontmatter
(name, description, metadata), and provides formatting helpers to inject skill
knowledge into the operator's prompt context.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("ralph-orchestrator.skills")


@dataclass
class SkillInfo:
    """Metadata and content for a single discovered skill."""

    name: str
    description: str
    path: Path
    content: str
    metadata: dict = field(default_factory=dict)
    emoji: str = ""
    homepage: str = ""


class SkillRegistry:
    """Discovers, loads, and formats skill documentation for prompt injection.

    Usage::

        registry = SkillRegistry(Path("skills"))
        prompt_section = registry.format_prompt_section()
        agent_prompt = base_prompt + "\\n\\n" + prompt_section

        # Or get a compact index for token-efficient context:
        index = registry.compact_index()

        # Or retrieve a specific skill's content:
        skill = registry.get("pumpfun")
    """

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir.resolve()
        self._skills: Dict[str, SkillInfo] = {}
        self._load_skills()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[SkillInfo]:
        """Return a single skill by its *name* field (or directory name)."""
        return self._skills.get(name)

    def list(self) -> List[SkillInfo]:
        """Return all discovered skills sorted by name."""
        return sorted(self._skills.values(), key=lambda s: s.name)

    @property
    def count(self) -> int:
        """Number of loaded skills."""
        return len(self._skills)

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def compact_index(self, indent: str = "") -> str:
        """Return a compact one-line-per-skill listing (name + emoji + desc).

        This is the most token-efficient way to include skills in an agent
        prompt — the agent can then ask for full content on specific skills.
        """
        lines: list[str] = []
        for info in self.list():
            emoji = info.emoji or "🛠️"
            lines.append(
                f"{indent}- **{info.name}** {emoji} — {info.description}"
            )
        return "\n".join(lines)

    def full_catalog(self) -> str:
        """Return the full content of every skill concatenated.

        WARNING: This can be *large* — only use when you know the target
        model has a very generous context window (e.g. Gemini 2M).
        """
        parts: list[str] = []
        for info in self.list():
            parts.append(f"# Skill: {info.name}")
            if info.emoji:
                parts.append(f"Emoji: {info.emoji}")
            parts.append(info.content)
            parts.append("---")
        return "\n".join(parts)

    def format_prompt_section(
        self,
        max_skills_detail: int = 5,
        max_desc_len: int = 100,
    ) -> str:
        """Return a markdown section suitable for appending to an agent prompt.

        Parameters
        ----------
        max_skills_detail:
            Number of skills to show full content for (0 = compact index only).
        max_desc_len:
            Truncate descriptions longer than this in the compact index.
        """
        if self.count == 0:
            return ""

        lines = [
            "## Available Skills",
            "",
            "The following skills / CLI tools are available on this system. "
            "Use them to accomplish tasks — you can run the CLI commands "
            "shown in each skill's documentation.",
            "",
        ]

        # Compact index (all skills)
        for info in self.list():
            emoji = info.emoji or "🛠️"
            desc = info.description
            if len(desc) > max_desc_len:
                desc = desc[:max_desc_len] + "…"
            lines.append(f"- `{info.name}` {emoji} {desc}")

        lines.append("")
        lines.append(
            f"*{self.count} skills loaded. "
            "Ask for details on any skill to see its full documentation.*"
        )

        # Full detail for the first N skills
        if max_skills_detail > 0:
            for info in self.list()[:max_skills_detail]:
                lines.append("")
                lines.append(f"### {info.name}")
                if info.homepage:
                    lines.append(f"Homepage: {info.homepage}")
                lines.append(info.content)

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<SkillRegistry({self.count} skills, dir={self.skills_dir})>"

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load_skills(self) -> None:
        """Scan *skills_dir* and load every ``SKILL.md`` found."""
        if not self.skills_dir.is_dir():
            logger.warning("Skills directory does not exist: %s", self.skills_dir)
            return

        for child in sorted(self.skills_dir.iterdir()):
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if not skill_file.is_file():
                continue
            try:
                raw = skill_file.read_text(encoding="utf-8")
                info = self._parse_skill(raw, child)
                if info is not None:
                    self._skills[info.name] = info
            except Exception:
                logger.exception("Failed to load skill from %s", child)

        logger.info("Loaded %d skills from %s", self.count, self.skills_dir)

    @staticmethod
    def _parse_skill(raw: str, path: Path) -> Optional[SkillInfo]:
        """Parse YAML frontmatter from a SKILL.md file.

        Minimal parser — we only extract ``name``, ``description``,
        ``homepage``, and ``metadata``.  The rest of the file is kept
        as markdown *content*.
        """
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
        if not m:
            return None

        front = m.group(1)
        body = raw[m.end() :].strip()

        # Minimal YAML key-value extraction (no full YAML dep needed)
        name = path.name  # fallback to directory name
        description = ""
        homepage = ""
        metadata: dict = {}
        meta_line_buffer = ""

        for line in front.split("\n"):
            stripped = line.strip()
            if stripped.startswith("name:"):
                name = stripped.split(":", 1)[1].strip().strip("\"'")
            elif stripped.startswith("description:"):
                description = stripped.split(":", 1)[1].strip().strip("\"'")
            elif stripped.startswith("homepage:"):
                homepage = stripped.split(":", 1)[1].strip().strip("\"'")
            elif stripped.startswith("metadata:"):
                meta_line_buffer = stripped.split(":", 1)[1].strip()
            # Handle metadata continuing on the same line as the key

        # Parse metadata JSON if present
        if meta_line_buffer:
            try:
                metadata = json.loads(meta_line_buffer)
            except json.JSONDecodeError:
                # Could span multiple lines — try reconstructing
                try:
                    meta_start = front.index("metadata:")
                    meta_raw = front[meta_start:].split("metadata:", 1)[1].strip()
                    metadata = json.loads(meta_raw)
                except (ValueError, json.JSONDecodeError):
                    pass

        emoji = metadata.get("clawdbot", {}).get("emoji", "")

        return SkillInfo(
            name=name,
            description=description,
            path=path,
            content=body,
            metadata=metadata,
            emoji=emoji,
            homepage=homepage,
        )
