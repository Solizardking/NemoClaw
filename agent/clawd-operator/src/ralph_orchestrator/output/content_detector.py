# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Content type detection for OpenClawd Operator output formatting."""

from __future__ import annotations

from enum import Enum


class ContentType(Enum):
    """Supported output content categories."""

    PLAIN_TEXT = "plain_text"
    DIFF = "diff"
    CODE_BLOCK = "code_block"
    MARKDOWN = "markdown"
    MARKDOWN_TABLE = "markdown_table"
    ERROR_TRACEBACK = "error_traceback"


class ContentDetector:
    """Detect common structured text forms from agent output."""

    def detect(self, text: str | None) -> ContentType:
        if not text or not text.strip():
            return ContentType.PLAIN_TEXT

        value = text.strip()
        if self.is_error_traceback(value):
            return ContentType.ERROR_TRACEBACK
        if self.is_diff(value):
            return ContentType.DIFF
        if self.is_markdown_table(value):
            return ContentType.MARKDOWN_TABLE
        if self.is_code_block(value):
            return ContentType.CODE_BLOCK
        if self.is_markdown(value):
            return ContentType.MARKDOWN
        return ContentType.PLAIN_TEXT

    @staticmethod
    def is_diff(text: str) -> bool:
        lines = text.splitlines()
        if any(line.startswith("diff --git ") for line in lines):
            return True
        return any(line.startswith("@@ ") for line in lines) and any(
            line.startswith(("+", "-")) and not line.startswith(("+++", "---")) for line in lines
        )

    @staticmethod
    def is_code_block(text: str) -> bool:
        if "```" in text:
            return True
        lines = text.splitlines()
        code_like = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("def ", "class ", "import ", "from ", "const ", "let ", "var ")):
                code_like += 1
            elif stripped.endswith(("{", "}", ";")):
                code_like += 1
            elif line.startswith(("    ", "\t")):
                code_like += 1
        return code_like >= 2

    @staticmethod
    def is_markdown_table(text: str) -> bool:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        return lines[0].startswith("|") and "|" in lines[0][1:] and set(lines[1]) <= {"|", "-", ":", " "}

    @staticmethod
    def is_markdown(text: str) -> bool:
        indicators = 0
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("# ", "## ", "### ", "- ", "* ", "1. ")):
                indicators += 1
            if "**" in stripped or "__" in stripped or "[" in stripped and "](" in stripped:
                indicators += 1
        return indicators >= 2

    @staticmethod
    def is_error_traceback(text: str) -> bool:
        return "Traceback (most recent call last):" in text or (
            "Error:" in text and any(line.strip().startswith("File ") for line in text.splitlines())
        )
