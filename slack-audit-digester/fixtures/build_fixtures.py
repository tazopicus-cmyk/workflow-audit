#!/usr/bin/env python3
"""Generate fake Slack fixtures. No real customer data."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANCHOR = datetime(2026, 9, 22, 18, 0, tzinfo=timezone.utc)

USERS = {
    "U01": "Maya Chen",
    "U02": "Jordan Blake",
    "U03": "Priya Shah",
    "U04": "Sam Ortiz",
    "U05": "Alex Nguyen",
    "U06": "Riley Cho",
}


def ts(days_ago: int, hour: int = 14, minute: int = 0, seq: int = 1) -> str:
    dt = ANCHOR - timedelta(days=days_ago)
    second = seq % 60
    micro = (seq * 1000) % 1_000_000
    dt = dt.replace(hour=hour, minute=minute % 60, second=second, microsecond=micro)
    return f"{dt.timestamp():.6f}"


def msg(
    days_ago: int,
    user: str,
    text: str,
    channel: str,
    hour: int = 14,
    minute: int = 0,
    seq: int = 1,
    **extra,
) -> dict:
    rec = {
        "type": "message",
        "user": user,
        "user_name": USERS.get(user, user),
        "text": text,
        "ts": ts(days_ago, hour, minute, seq),
        "channel": channel,
    }
    rec.update(extra)
    return rec


def write_workspace(out_dir: Path, messages: list[dict], channels: list[tuple[str, str]]) -> None:
    slack = out_dir / "slack"
    if slack.exists():
        for path in slack.rglob("*"):
            if path.is_file():
                path.unlink()
    slack.mkdir(parents=True, exist_ok=True)

    (slack / "users.json").write_text(
        json.dumps(
            [{"id": uid, "name": name.split()[0].lower(), "real_name": name} for uid, name in USERS.items()],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (slack / "channels.json").write_text(
        json.dumps([{"id": cid, "name": name} for cid, name in channels], indent=2) + "\n",
        encoding="utf-8",
    )

    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rec in messages:
        day = datetime.fromtimestamp(float(rec["ts"]), tz=timezone.utc).strftime("%Y-%m-%d")
        by_key[(rec["channel"], day)].append(rec)

    for (channel, day), rows in sorted(by_key.items()):
        folder = slack / channel
        folder.mkdir(parents=True, exist_ok=True)
        # Workspace daily files usually omit channel on each message.
        payload = [{k: v for k, v in row.items() if k != "channel"} for row in rows]
        (folder / f"{day}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(out_dir: Path, filename: str, messages: list[dict]) -> None:
    slack = out_dir / "slack"
    slack.mkdir(parents=True, exist_ok=True)
    path = slack / filename
    with path.open("w", encoding="utf-8") as fh:
        for rec in messages:
            fh.write(json.dumps(rec) + "\n")


def build_rich() -> None:
    out = ROOT / "rich-45d"
    out.mkdir(parents=True, exist_ok=True)
    (out / "intake.json").write_text(
        json.dumps(
            {
                "name": "Maya Chen",
                "email": "maya@northline.test",
                "company": "Northline Outfitters",
                "area": "customer support",
                "channels": ["support", "support-escalations"],
                "workspace": "Invite was to #support and #support-escalations only.",
                "notes": "Wholesale VIP tickets keep slipping. Refund how-to is the loudest loop.",
                "sku": "slack-opportunity-audit",
                "purchased_forward_watch": False,
                "lookback_days_requested": 45,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    m: list[dict] = []
    seq = 1

    def add(*args, **kwargs):
        nonlocal seq
        kwargs.setdefault("seq", seq)
        seq += 1
        m.append(msg(*args, **kwargs))

    # --- Refund FAQ across many days ---
    refund_days = [0, 2, 5, 8, 11, 14, 18, 21, 25, 28, 33, 37, 41]
    refund_lines = [
        "Customer asked again: how do I request a refund on order {n}?",
        "Refund question in the queue. What is the refund window for order {n}?",
        "How do I request a refund if the jacket was worn once? Order {n}.",
        "Same refund how-to. Customer wants a refund on order {n}. Do we still offer store credit?",
        "Repeat: how do I request a refund, and where is the form? Order {n}.",
    ]
    for i, d in enumerate(refund_days):
        add(d, "U02", refund_lines[i % len(refund_lines)].format(n=4400 + i), "support", hour=11, minute=i)

    # --- Shipping / tracking FAQ ---
    ship_days = [1, 3, 6, 9, 12, 16, 19, 23, 27, 31, 36, 40]
    ship_lines = [
        "Where is this order? Tracking for {n} is not updating.",
        "Customer asking for shipping ETA on order {n}. Where is the package?",
        "Tracking number for order {n} looks stale. Where is this order supposed to be?",
        "How do we quote shipping ETA when tracking for {n} is blank?",
        "Where is order {n}? Delivery was due yesterday and tracking did not move.",
    ]
    for i, d in enumerate(ship_days):
        add(d, "U03", ship_lines[i % len(ship_lines)].format(n=8800 + i), "support", hour=13, minute=i * 2)

    # --- Login / password FAQ ---
    login_days = [0, 4, 10, 17, 24, 32, 39]
    login_lines = [
        "How do I reset a password for a wholesale login? Account locked out again.",
        "Customer cannot login. Password reset email never arrives. How do I reset a password here?",
        "Repeat login issue. Locked out after three tries. How do I reset a password?",
        "Wholesale portal login failed. How do I reset a password without wiping the account?",
        "How do I reset a password when the customer has no access to the old email?",
    ]
    for i, d in enumerate(login_days):
        add(d, "U05", login_lines[i % len(login_lines)], "support", hour=15, minute=i)

    # --- Handoffs ---
    handoff_days = [0, 1, 4, 7, 13, 15, 20, 26, 30, 35, 42]
    handoff_lines = [
        ("support", "U02", "Can you take this VIP thread <@U03>? They are asking for a make-good."),
        ("support", "U03", "Handing this off to escalations. Can someone grab the wholesale quote?"),
        ("support-escalations", "U04", "Looping in <@U01>. Can you take this from Jordan?"),
        ("support", "U05", "Passing this to <@U04>. Can you take the damaged-goods case?"),
        ("support-escalations", "U01", "Routing this to Priya. Can you take ownership so the ping stops?"),
        ("support", "U02", "Moving this to #support-escalations. Can you take it Sam?"),
        ("support-escalations", "U03", "Over to you <@U01>. Handing this off, the customer is repeating themselves."),
        ("support", "U06", "Can someone take this? I am looping in Maya for the return exception."),
        ("support-escalations", "U04", "Can you take this chargeback thread? Passing this to Maya."),
        ("support", "U02", "Please take the school-order mess <@U03>. Handing this off before EOD."),
        ("support-escalations", "U01", "Can you take this from Alex and record an owner?"),
    ]
    for i, d in enumerate(handoff_days):
        ch, user, text = handoff_lines[i % len(handoff_lines)]
        add(d, user, text, ch, hour=16, minute=3 + i)

    # --- Status pings ---
    ping_days = [0, 2, 6, 9, 14, 18, 22, 29, 34, 38]
    ping_lines = [
        "Any update on ticket 882? Customer is still waiting.",
        "Checking in on the wholesale quote. Any update on ticket 910?",
        "Following up. Status on order 4419? Still waiting from Friday.",
        "Bump this. Any update on ticket 773 for the lodge order?",
        "Checking in again. Status on the replacement for ticket 882?",
        "Any update on ticket 1204? Sales is still waiting on a ship date.",
        "Following up on ticket 910. Any update before the buyer call?",
        "Still waiting. Status on the warranty ticket 556?",
        "Ping on ticket 882. Any update, or is this blocked?",
        "Checking in on ticket 773. Any update for the school order?",
    ]
    for i, d in enumerate(ping_days):
        add(d, "U06", ping_lines[i], "support", hour=10, minute=20 + i)

    # --- Standup / status theater (many distinct days) ---
    standup_days = list(range(0, 45, 2))[:16]
    for i, d in enumerate(standup_days):
        closed = 4 + (i % 5)
        add(
            d,
            "U02",
            f"Standup: yesterday I closed {closed} tickets. Today I will work the VIP queue. No blockers.",
            "support",
            hour=9,
            minute=5,
        )
        if i % 2 == 0:
            add(
                d,
                "U03",
                f"Standup: yesterday I finished the queue sweep. Today I will draft macros. No blocker besides the lodge order.",
                "support",
                hour=9,
                minute=8,
            )

    # --- Approvals ---
    approval_days = [3, 8, 12, 21, 27, 36]
    approval_lines = [
        "Need a yes on the 15 percent goodwill. Can I proceed, or do you need to sign off?",
        "Ok to send the replacement without a return? Need a green light from Maya.",
        "Can I proceed with store credit on order 4412? Need approval before I reply.",
        "Need you to sign off on waving restocking for the school order.",
        "Green light needed. Can I proceed with the wholesale make-good?",
        "Need a yes. Approve the overnight reship before 3pm?",
    ]
    for i, d in enumerate(approval_days):
        add(d, "U03", approval_lines[i], "support-escalations", hour=17, minute=i)

    # --- Angry / legal (keep-human signal, not a cluster) ---
    add(
        5,
        "U04",
        "Customer is furious and mentioned a lawsuit on the damaged tent. Do not draft this one.",
        "support-escalations",
        hour=12,
        minute=40,
    )

    # --- Noise that should not form a fake cluster ---
    add(1, "U01", "Thanks Jordan. I saw the lodge note.", "support", hour=18)
    add(7, "U05", "Lunch cover from 1 to 2.", "support", hour=12)
    add(19, "U06", "I am out Friday. Cover is Priya.", "support", hour=8)

    # --- Bot / system (must be stripped) ---
    m.append(
        {
            "type": "message",
            "subtype": "channel_join",
            "user": "U06",
            "user_name": "Riley Cho",
            "text": "<@U06> has joined the channel",
            "ts": ts(2, 9, 0, 1),
            "channel": "support",
        }
    )
    m.append(
        {
            "type": "message",
            "subtype": "bot_message",
            "bot_id": "B01",
            "user": "U00",
            "user_name": "pagerbot",
            "text": "Nightly ticket dump: 42 open.",
            "ts": ts(1, 7, 0, 1),
            "channel": "support",
        }
    )

    write_workspace(out, m, [("C01", "support"), ("C02", "support-escalations")])
    print(f"rich: {len(m)} raw messages -> {out}")


def build_thin() -> None:
    out = ROOT / "thin-history"
    out.mkdir(parents=True, exist_ok=True)
    (out / "intake.json").write_text(
        json.dumps(
            {
                "name": "Lee Park",
                "email": "lee@littleharbor.test",
                "company": "Little Harbor Studio",
                "area": "client onboarding",
                "channels": "ops",
                "workspace": "Free Slack, quiet workspace.",
                "notes": "We only started using #ops last month.",
                "sku": "slack-opportunity-audit",
                "purchased_forward_watch": False,
                "lookback_days_requested": 45,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Newest cluster is sparse. A few older messages exist so lookback extends toward 90,
    # then still fails the thin bar.
    messages = [
        msg(1, "U01", "Posted the onboarding checklist.", "ops", hour=11),
        msg(1, "U02", "Got it.", "ops", hour=11, minute=4),
        msg(3, "U01", "Client sent brand colors.", "ops", hour=15),
        msg(4, "U03", "I will add them to the folder later.", "ops", hour=16),
        msg(8, "U01", "Kickoff is Thursday.", "ops", hour=10),
        msg(8, "U02", "I can join.", "ops", hour=10, minute=6),
        msg(12, "U01", "Invoice went out.", "ops", hour=9),
        msg(18, "U03", "Thanks.", "ops", hour=13),
        msg(22, "U02", "Out tomorrow.", "ops", hour=17),
        msg(22, "U01", "Covering.", "ops", hour=17, minute=3),
        # Older than 45 days, inside 90, still not enough volume or days.
        msg(52, "U01", "Channel created. We will try to keep client notes here.", "ops", hour=12),
        msg(61, "U02", "Ok.", "ops", hour=12, minute=2),
        msg(70, "U01", "Parking this until the first paid job lands.", "ops", hour=14),
        {
            "type": "message",
            "subtype": "channel_join",
            "user": "U03",
            "text": "<@U03> has joined the channel",
            "ts": ts(70, 14, 1, 1),
            "channel": "ops",
        },
    ]
    write_jsonl(out, "ops.jsonl", messages)
    print(f"thin: {len(messages)} raw messages -> {out}")


if __name__ == "__main__":
    build_rich()
    build_thin()
