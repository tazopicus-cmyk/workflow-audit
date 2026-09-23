"""Load intake.json and Slack export files (offline, no API)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from slack_audit_digest.constants import BOT_USER_IDS, SKU_DEFAULT, SYSTEM_SUBTYPES
from slack_audit_digest.models import Intake, Message

_SKIP_FILENAMES = frozenset(
    {
        "integration_logs.json",
        "canvases.json",
        "lists.json",
        "file_conversations.json",
    }
)

_USER_INDEX_NAMES = frozenset({"users.json", "users.json.json"})
_CHANNEL_INDEX_NAMES = frozenset({"channels.json", "groups.json", "mpims.json", "dms.json"})


def load_intake(path: Path) -> Intake:
    if not path.is_file():
        raise FileNotFoundError(f"missing intake.json: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("intake.json must be a JSON object")

    name = str(raw.get("name") or "").strip()
    email = str(raw.get("email") or "").strip()
    if not name:
        raise ValueError("intake.json missing required field: name")
    if not email:
        raise ValueError("intake.json missing required field: email")

    channels = _normalize_channels(raw.get("channels"))
    lookback = raw.get("lookback_days_requested", 45)
    try:
        lookback_i = int(lookback)
    except (TypeError, ValueError) as exc:
        raise ValueError("lookback_days_requested must be an integer") from exc

    return Intake(
        name=name,
        email=email,
        company=str(raw.get("company") or "").strip(),
        area=str(raw.get("area") or "").strip(),
        channels=channels,
        workspace=str(raw.get("workspace") or "").strip(),
        notes=str(raw.get("notes") or "").strip(),
        sku=str(raw.get("sku") or SKU_DEFAULT).strip() or SKU_DEFAULT,
        purchased_forward_watch=_as_bool(raw.get("purchased_forward_watch", False)),
        lookback_days_requested=lookback_i,
        raw=raw,
    )


def load_slack_export(slack_dir: Path) -> list[Message]:
    if not slack_dir.is_dir():
        raise FileNotFoundError(f"missing slack/ directory: {slack_dir}")

    users = _load_users(slack_dir)
    channel_names = _load_channel_index(slack_dir)
    messages: list[Message] = []

    for path in sorted(slack_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.name in _SKIP_FILENAMES:
            continue
        if path.name in _USER_INDEX_NAMES or path.name in _CHANNEL_INDEX_NAMES:
            continue
        if path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        messages.extend(_load_file(path, slack_dir, users, channel_names))

    if not messages:
        raise ValueError(f"no Slack messages found under {slack_dir}")
    messages.sort(key=lambda m: (m.ts, m.channel, m.text))
    return messages


def _normalize_channels(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [_clean_channel(str(v)) for v in value if str(v).strip()]
    text = str(value).strip()
    parts = re.split(r"[,;\n]+", text)
    return [_clean_channel(p) for p in parts if p.strip()]


def _clean_channel(name: str) -> str:
    name = name.strip().lstrip("#").strip()
    return name


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_users(slack_dir: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in ("users.json", "users.json.json"):
        path = slack_dir / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows = data if isinstance(data, list) else data.get("members") or data.get("users") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("id") or "").strip()
            profile = row.get("profile") if isinstance(row.get("profile"), dict) else {}
            display = (
                str(row.get("real_name") or "").strip()
                or str(profile.get("real_name") or "").strip()
                or str(row.get("name") or "").strip()
                or uid
            )
            if uid:
                mapping[uid] = display
    return mapping


def _load_channel_index(slack_dir: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in ("channels.json", "groups.json"):
        path = slack_dir / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows = data if isinstance(data, list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("id") or "").strip()
            cname = _clean_channel(str(row.get("name") or ""))
            if cid and cname:
                mapping[cid] = cname
    return mapping


def _load_file(
    path: Path,
    slack_dir: Path,
    users: dict[str, str],
    channel_names: dict[str, str],
) -> list[Message]:
    channel_guess = _channel_from_path(path, slack_dir)
    text = path.read_text(encoding="utf-8")
    records: list[Any]
    if path.suffix.lower() == ".jsonl" or path.name.endswith(".jsonl"):
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    else:
        data = json.loads(text)
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and isinstance(data.get("messages"), list):
            records = data["messages"]
            if not channel_guess:
                channel_guess = _clean_channel(str(data.get("channel") or data.get("name") or ""))
        else:
            return []

    out: list[Message] = []
    for rec in records:
        msg = _parse_message(rec, channel_guess, users, channel_names, str(path.relative_to(slack_dir)))
        if msg is not None:
            out.append(msg)
    return out


def _channel_from_path(path: Path, slack_dir: Path) -> str:
    rel = path.relative_to(slack_dir)
    if len(rel.parts) >= 2:
        return _clean_channel(rel.parts[0])
    return _clean_channel(path.stem)


def _parse_ts(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        # Slack milliseconds accidentally stored?
        if ts > 1e12:
            ts = ts / 1000.0
        return ts
    text = str(value).strip()
    if not text:
        return None
    try:
        ts = float(text)
    except ValueError:
        return None
    if ts > 1e12:
        ts = ts / 1000.0
    return ts


def _parse_message(
    rec: Any,
    channel_guess: str,
    users: dict[str, str],
    channel_names: dict[str, str],
    source_file: str,
) -> Message | None:
    if not isinstance(rec, dict):
        return None
    msg_type = str(rec.get("type") or "message")
    if msg_type not in {"message", ""}:
        return None

    ts = _parse_ts(rec.get("ts") or rec.get("timestamp") or rec.get("event_ts"))
    if ts is None:
        return None

    text = str(rec.get("text") or rec.get("message") or "")
    subtype = rec.get("subtype")
    subtype_s = str(subtype) if subtype else None
    user_id = str(rec.get("user") or rec.get("user_id") or "").strip()
    user_name = (
        str(rec.get("user_name") or rec.get("username") or rec.get("real_name") or "").strip()
        or users.get(user_id, "")
        or user_id
        or "unknown"
    )

    channel = (
        _clean_channel(str(rec.get("channel_name") or rec.get("channel_id") or rec.get("channel") or ""))
        or channel_guess
    )
    if channel in channel_names:
        channel = channel_names[channel]
    if not channel:
        channel = "unknown"

    bot_id = rec.get("bot_id") or rec.get("app_id")
    is_bot_user = user_id in BOT_USER_IDS or str(rec.get("user") or "") == "USLACKBOT"
    is_human = (
        not bot_id
        and not is_bot_user
        and (subtype_s is None or subtype_s not in SYSTEM_SUBTYPES)
        and bool(text.strip())
    )

    thread_ts = rec.get("thread_ts")
    thread_s = str(thread_ts) if thread_ts else None

    return Message(
        ts=ts,
        text=text,
        user=user_id or user_name,
        user_name=user_name,
        channel=channel,
        thread_ts=thread_s,
        is_human=is_human,
        subtype=subtype_s,
        source_file=source_file,
    )
