from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Literal

PathName = Literal["rich", "extended", "insufficient"]


@dataclass
class Intake:
    name: str
    email: str
    company: str = ""
    area: str = ""
    channels: list[str] = field(default_factory=list)
    workspace: str = ""
    notes: str = ""
    sku: str = "slack-opportunity-audit"
    purchased_forward_watch: bool = False
    lookback_days_requested: int = 45
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    ts: float
    text: str
    user: str
    user_name: str
    channel: str
    thread_ts: str | None = None
    is_human: bool = True
    subtype: str | None = None
    source_file: str = ""

    @property
    def when(self) -> datetime:
        return datetime.fromtimestamp(self.ts, tz=timezone.utc)

    @property
    def day(self) -> date:
        return self.when.date()


@dataclass
class Cluster:
    key: str
    kind: str  # faq, handoff, status_ping, status_theater, approval, other
    title_hint: str
    messages: list[Message] = field(default_factory=list)
    topic_terms: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.messages)

    @property
    def days(self) -> set[date]:
        return {m.day for m in self.messages}

    @property
    def channels(self) -> list[str]:
        seen: list[str] = []
        for m in self.messages:
            if m.channel not in seen:
                seen.append(m.channel)
        return seen

    @property
    def score(self) -> float:
        return float(self.count * max(len(self.days), 1))


@dataclass
class Opportunity:
    rank: int
    title: str
    trigger: str
    bot_role: str
    keep_human_gate: str
    kind: str
    evidence_count: int
    evidence_days: int
    channels: list[str]
    example: str = ""


@dataclass
class AnalysisResult:
    path: PathName
    window_days: int
    lookback_days_requested: int
    newest_ts: float
    window_start_ts: float
    window_end_ts: float
    human_messages: list[Message]
    all_in_window: list[Message]
    distinct_active_days: int
    channel_counts: dict[str, int]
    opportunities: list[Opportunity]
    seats: list[str]
    do_not_automate: list[str]
    capture_next: list[str]
    notes_internal: list[str] = field(default_factory=list)
    extended_from_thin: bool = False
    llm_enrich: bool = False
