"""Apply locked lookback rules: 45 days, extend toward 90 if thin, never unbounded."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from slack_audit_digest.constants import (
    DEFAULT_LOOKBACK_DAYS,
    MAX_LOOKBACK_DAYS,
    THIN_ACTIVE_DAYS,
    THIN_HUMAN_MESSAGES,
)
from slack_audit_digest.models import Message, PathName


def clamp_lookback_days(requested: int) -> int:
    if requested <= 0:
        return DEFAULT_LOOKBACK_DAYS
    return min(requested, MAX_LOOKBACK_DAYS)


def is_thin(human_count: int, active_days: int) -> bool:
    return human_count < THIN_HUMAN_MESSAGES or active_days < THIN_ACTIVE_DAYS


def newest_ts(messages: list[Message]) -> float:
    return max(m.ts for m in messages)


def human_in_window(messages: list[Message], start_ts: float, end_ts: float) -> list[Message]:
    return [
        m
        for m in messages
        if m.is_human and m.text.strip() and start_ts <= m.ts <= end_ts
    ]


def distinct_days(messages: list[Message]) -> int:
    return len({m.day for m in messages})


def apply_lookback(
    messages: list[Message],
    lookback_days_requested: int = DEFAULT_LOOKBACK_DAYS,
) -> tuple[PathName, int, float, float, float, list[Message], list[Message], bool]:
    """Return path, window_days, newest, start, end, humans, all_in_window, extended_from_thin."""
    requested = clamp_lookback_days(lookback_days_requested)
    newest = newest_ts(messages)
    end_ts = newest

    def slice_window(days: int) -> tuple[list[Message], list[Message], float]:
        start = newest - timedelta(days=days).total_seconds()
        all_in = [m for m in messages if start <= m.ts <= end_ts]
        humans = human_in_window(messages, start, end_ts)
        return humans, all_in, start

    humans45, all45, start45 = slice_window(requested)
    thin45 = is_thin(len(humans45), distinct_days(humans45))

    if not thin45:
        return "rich", requested, newest, start45, end_ts, humans45, all45, False

    older_exist = any(m.ts < start45 for m in messages)
    can_extend = requested < MAX_LOOKBACK_DAYS and older_exist
    if can_extend:
        humans90, all90, start90 = slice_window(MAX_LOOKBACK_DAYS)
        thin90 = is_thin(len(humans90), distinct_days(humans90))
        if thin90:
            return "insufficient", MAX_LOOKBACK_DAYS, newest, start90, end_ts, humans90, all90, True
        return "extended", MAX_LOOKBACK_DAYS, newest, start90, end_ts, humans90, all90, True

    return "insufficient", requested, newest, start45, end_ts, humans45, all45, False


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_date(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
