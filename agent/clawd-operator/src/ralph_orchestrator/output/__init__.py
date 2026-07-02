# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Console and formatter helpers for OpenClawd Operator."""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .content_detector import ContentDetector, ContentType

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, TextColumn

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover - depends on optional rich install
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    BarColumn = None  # type: ignore[assignment]
    RICH_AVAILABLE = False


class VerbosityLevel(Enum):
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class MessageType(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    INFO = "info"
    PROGRESS = "progress"


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str | None = None
    session_input_tokens: int = 0
    session_output_tokens: int = 0
    session_total_tokens: int = 0
    session_cost: float = 0.0

    def add(self, input_tokens: int = 0, output_tokens: int = 0, cost: float = 0.0, model: str | None = None) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.cost = cost
        self.model = model
        self.session_input_tokens += input_tokens
        self.session_output_tokens += output_tokens
        self.session_total_tokens += input_tokens + output_tokens
        self.session_cost += cost

    def reset_current(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.cost = 0.0
        self.model = None


@dataclass
class ToolCallInfo:
    tool_name: str
    tool_id: str
    input_params: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: Any = None
    is_error: bool = False
    duration_ms: int | None = None


@dataclass
class FormatContext:
    iteration: int = 0
    verbosity: VerbosityLevel = VerbosityLevel.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffStats:
    additions: int = 0
    deletions: int = 0
    files: int = 0
    files_changed: dict[str, tuple[int, int]] = field(default_factory=dict)


class DiffFormatter:
    """Small diff helper used by the console."""

    def __init__(self, console: Any = None):
        self.console = console

    def _calculate_stats(self, lines: list[str]) -> DiffStats:
        stats = DiffStats()
        current_file: str | None = None
        for line in lines:
            if line.startswith("diff --git "):
                current_file = self._extract_filename(line)
                if current_file not in stats.files_changed:
                    stats.files_changed[current_file] = (0, 0)
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                stats.additions += 1
                if current_file:
                    adds, dels = stats.files_changed[current_file]
                    stats.files_changed[current_file] = (adds + 1, dels)
            elif line.startswith("-"):
                stats.deletions += 1
                if current_file:
                    adds, dels = stats.files_changed[current_file]
                    stats.files_changed[current_file] = (adds, dels + 1)
        stats.files = len(stats.files_changed)
        return stats

    @staticmethod
    def _extract_filename(line: str) -> str:
        parts = line.split()
        if len(parts) >= 4 and parts[3].startswith("b/"):
            return parts[3][2:]
        return parts[-1].removeprefix("b/") if parts else ""

    @staticmethod
    def _is_binary_file(line: str) -> bool:
        binary_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".pdf", ".bin")
        return line.lower().endswith(binary_exts)

    @staticmethod
    def _format_hunk_header(line: str) -> str:
        marker = line.split("@@")
        context = marker[-1].strip() if len(marker) >= 3 else ""
        range_part = marker[1].strip() if len(marker) >= 3 else ""
        start = range_part.split()[0].lstrip("-").split(",")[0] if range_part else "?"
        suffix = f" {context}" if context else ""
        return f"Lines {start}-{suffix}"


class OutputFormatter:
    """Base formatter with common display gating and callback handling."""

    def __init__(self, verbosity: VerbosityLevel = VerbosityLevel.NORMAL):
        self.verbosity = verbosity
        self.token_usage = TokenUsage()
        self._callbacks: list[Callable[[MessageType, str, FormatContext], None]] = []

    def should_display(self, message_type: MessageType) -> bool:
        if message_type is MessageType.ERROR:
            return True
        if self.verbosity is VerbosityLevel.QUIET:
            return False
        if self.verbosity in (VerbosityLevel.VERBOSE, VerbosityLevel.DEBUG):
            return True
        return message_type in {MessageType.ASSISTANT, MessageType.TOOL_CALL, MessageType.TOOL_RESULT, MessageType.PROGRESS}

    def register_callback(self, callback: Callable[[MessageType, str, FormatContext], None]) -> None:
        self._callbacks.append(callback)

    def _notify(self, message_type: MessageType, output: str, iteration: int = 0) -> None:
        ctx = FormatContext(iteration=iteration, verbosity=self.verbosity, token_usage=self.token_usage)
        for callback in self._callbacks:
            try:
                callback(message_type, output, ctx)
            except Exception:
                continue

    def update_tokens(self, input_tokens: int = 0, output_tokens: int = 0, cost: float = 0.0, model: str | None = None) -> None:
        self.token_usage.add(input_tokens=input_tokens, output_tokens=output_tokens, cost=cost, model=model)

    @staticmethod
    def summarize_content(content: Any, max_length: int = 1000) -> str:
        text = str(content)
        if len(text) <= max_length:
            return text
        return f"{text[:max_length]}... (truncated)"


class PlainTextFormatter(OutputFormatter):
    def format_tool_call(self, tool_info: ToolCallInfo, iteration: int = 0) -> str:
        if not self.should_display(MessageType.TOOL_CALL):
            return ""
        params = self.summarize_content(json.dumps(tool_info.input_params, default=str), 500)
        output = f"TOOL CALL: {tool_info.tool_name} [{tool_info.tool_id[:12]}] {params}"
        self._notify(MessageType.TOOL_CALL, output, iteration)
        return output

    def format_tool_result(self, tool_info: ToolCallInfo, iteration: int = 0) -> str:
        if not self.should_display(MessageType.TOOL_RESULT):
            return ""
        status = "ERROR" if tool_info.is_error else "Success"
        duration = f" {tool_info.duration_ms}ms" if tool_info.duration_ms is not None else ""
        result = self.summarize_content(tool_info.result, 1000)
        output = f"TOOL RESULT: {tool_info.tool_name}{duration} {status}\n{result}"
        self._notify(MessageType.TOOL_RESULT, output, iteration)
        return output

    def format_assistant_message(self, message: str, iteration: int = 0) -> str:
        if not self.should_display(MessageType.ASSISTANT):
            return ""
        body = self.summarize_content(message, 1000)
        output = f"ASSISTANT: {body}"
        self._notify(MessageType.ASSISTANT, output, iteration)
        return output

    def format_system_message(self, message: str, iteration: int = 0) -> str:
        if not self.should_display(MessageType.SYSTEM):
            return ""
        output = f"SYSTEM: {message}"
        self._notify(MessageType.SYSTEM, output, iteration)
        return output

    def format_error(self, message: str, iteration: int = 0, exception: Exception | None = None) -> str:
        details = f"\n{traceback.format_exc()}" if exception and self.verbosity.value >= VerbosityLevel.VERBOSE.value else ""
        output = f"ERROR{f' [{iteration}]' if iteration else ''}: {message}{details}"
        self._notify(MessageType.ERROR, output, iteration)
        return output

    def format_progress(self, message: str, current: int = 0, total: int = 0, iteration: int = 0) -> str:
        if not self.should_display(MessageType.PROGRESS):
            return ""
        percent = f" {int((current / total) * 100)}%" if total > 0 else ""
        output = f"PROGRESS: {message}{percent}"
        self._notify(MessageType.PROGRESS, output, iteration)
        return output

    def format_token_usage(self) -> str:
        usage = self.token_usage
        model = f" {usage.model}" if usage.model else ""
        return f"TOKENS{model}: {usage.total_tokens} (${usage.cost:.4f})"

    def format_section_header(self, title: str, iteration: int = 0) -> str:
        prefix = f"Iteration {iteration}: " if iteration else ""
        return f"== {prefix}{title} =="

    def format_section_footer(self) -> str:
        return "== done =="


class RichTerminalFormatter(PlainTextFormatter):
    def __init__(self, verbosity: VerbosityLevel = VerbosityLevel.NORMAL, smart_detection: bool = True):
        super().__init__(verbosity=verbosity)
        self.console = Console() if RICH_AVAILABLE else None
        self._smart_detection = smart_detection
        self._content_detector = ContentDetector() if smart_detection else None

    def print(self, value: str) -> None:
        if self.console:
            self.console.print(value)
        else:
            print(value)

    def print_panel(self, content: str, title: str | None = None, border_style: str = "blue") -> None:
        if self.console and Panel:
            self.console.print(Panel(content, title=title, border_style=border_style))
        else:
            print(content)

    def create_progress_bar(self) -> Any:
        if RICH_AVAILABLE and Progress:
            return Progress(TextColumn("{task.description}"), BarColumn())
        return None

    def print_smart(self, text: str) -> None:
        if self.should_display(MessageType.ASSISTANT):
            self.print(self._render_smart_content(text, self._content_detector.detect(text) if self._content_detector else ContentType.PLAIN_TEXT))

    def _render_smart_content(self, text: str, _content_type: ContentType) -> str:
        return self._preprocess_markdown(text)

    @staticmethod
    def _preprocess_markdown(text: str) -> str:
        return text.replace("- [ ]", "- \u2610").replace("- [x]", "- \u2611").replace("- [X]", "- \u2611")


class JsonFormatter(OutputFormatter):
    def __init__(self, verbosity: VerbosityLevel = VerbosityLevel.NORMAL, pretty: bool = False):
        super().__init__(verbosity=verbosity)
        self.pretty = pretty
        self._events: list[dict[str, Any]] = []

    def _event(self, message_type: MessageType, payload: dict[str, Any], iteration: int = 0) -> str:
        if not self.should_display(message_type):
            return ""
        event = {
            "type": message_type.value,
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            **payload,
        }
        self._events.append(event)
        output = json.dumps(event, indent=2 if self.pretty else None, default=str)
        self._notify(message_type, output, iteration)
        return output

    def format_tool_call(self, tool_info: ToolCallInfo, iteration: int = 0) -> str:
        return self._event(MessageType.TOOL_CALL, {"tool_name": tool_info.tool_name, "tool_id": tool_info.tool_id, "input": tool_info.input_params}, iteration)

    def format_tool_result(self, tool_info: ToolCallInfo, iteration: int = 0) -> str:
        return self._event(MessageType.TOOL_RESULT, {"tool_name": tool_info.tool_name, "tool_id": tool_info.tool_id, "result": self.summarize_content(tool_info.result), "is_error": tool_info.is_error}, iteration)

    def format_assistant_message(self, message: str, iteration: int = 0) -> str:
        return self._event(MessageType.ASSISTANT, {"message": self.summarize_content(message)}, iteration)

    def format_system_message(self, message: str, iteration: int = 0) -> str:
        return self._event(MessageType.SYSTEM, {"message": message}, iteration)

    def format_error(self, message: str, iteration: int = 0, exception: Exception | None = None) -> str:
        payload: dict[str, Any] = {"message": message}
        if exception:
            payload["exception"] = str(exception)
        return self._event(MessageType.ERROR, payload, iteration)

    def format_progress(self, message: str, current: int = 0, total: int = 0, iteration: int = 0) -> str:
        return self._event(MessageType.PROGRESS, {"message": message, "current": current, "total": total}, iteration)

    def format_token_usage(self) -> str:
        return self._event(MessageType.INFO, {"token_usage": self.token_usage.__dict__})

    def format_section_header(self, title: str, iteration: int = 0) -> str:
        return self._event(MessageType.INFO, {"section": title}, iteration)

    def format_section_footer(self) -> str:
        return self._event(MessageType.INFO, {"section": "done"})

    def get_events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()

    def get_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self._events:
            counts[event["type"]] = counts.get(event["type"], 0) + 1
        return counts

    def export_events(self) -> str:
        return json.dumps(self._events, indent=2 if self.pretty else None, default=str)


class RalphConsole:
    PROGRESS_BAR_WIDTH = 30

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.diff_formatter = DiffFormatter(self.console) if RICH_AVAILABLE else None

    def _print(self, message: str) -> None:
        if self.console:
            self.console.print(message)
        else:
            print(message)

    def print_status(self, message: str, style: str | None = None) -> None:
        self._print(message)

    def print_success(self, message: str) -> None:
        self._print(message)

    def print_error(self, message: str, severity: str = "error") -> None:
        self._print(f"{severity}: {message}")

    def print_warning(self, message: str) -> None:
        self._print(f"warning: {message}")

    def print_info(self, message: str) -> None:
        self._print(message)

    def print_header(self, message: str) -> None:
        self._print(message)

    def print_message(self, message: str) -> None:
        self._print(message)

    def print_separator(self) -> None:
        self._print("-" * self.PROGRESS_BAR_WIDTH)

    def print_iteration_header(self, iteration: int) -> None:
        self.print_header(f"Iteration {iteration}")

    def print_stats(self, **stats: Any) -> None:
        for key, value in stats.items():
            self.print_info(f"{key}: {value}")

    def print_countdown(self, remaining: int, total: int) -> None:
        progress = 1.0 if total <= 0 else max(0.0, min(1.0, (total - remaining) / total))
        filled = int(self.PROGRESS_BAR_WIDTH * progress)
        self._print("[" + "#" * filled + "-" * (self.PROGRESS_BAR_WIDTH - filled) + "]")

    @staticmethod
    def _is_diff_content(text: str) -> bool:
        return ContentDetector.is_diff(text)

    @staticmethod
    def _is_markdown_table(text: str) -> bool:
        return ContentDetector.is_markdown_table(text)

    @staticmethod
    def _is_markdown_content(text: str) -> bool:
        return ContentDetector.is_markdown(text)

    @staticmethod
    def _is_error_traceback(text: str) -> bool:
        return ContentDetector.is_error_traceback(text)

    @staticmethod
    def _preprocess_markdown(text: str) -> str:
        return RichTerminalFormatter._preprocess_markdown(text)


def create_formatter(format_type: str = "rich", verbosity: VerbosityLevel = VerbosityLevel.NORMAL) -> OutputFormatter:
    normalized = format_type.lower()
    if normalized in {"plain", "text"}:
        return PlainTextFormatter(verbosity=verbosity)
    if normalized in {"rich", "terminal"}:
        return RichTerminalFormatter(verbosity=verbosity)
    if normalized == "json":
        return JsonFormatter(verbosity=verbosity)
    raise ValueError(f"Unknown output format: {format_type}")


__all__ = [
    "ContentDetector",
    "ContentType",
    "DiffFormatter",
    "DiffStats",
    "FormatContext",
    "JsonFormatter",
    "MessageType",
    "OutputFormatter",
    "PlainTextFormatter",
    "RICH_AVAILABLE",
    "RalphConsole",
    "RichTerminalFormatter",
    "TokenUsage",
    "ToolCallInfo",
    "VerbosityLevel",
    "create_formatter",
]
