"""Render opportunity-draft.md from analysis. Client-facing. No em dashes. No prompt packs."""

from __future__ import annotations

from slack_audit_digest.constants import (
    AUDIT_PRICE,
    DEFAULT_LOOKBACK_DAYS,
    FORWARD_WATCH_DURATION,
    FORWARD_WATCH_PRICE,
    FORWARD_WATCH_URL,
    MAX_LOOKBACK_DAYS,
    SETUP_CREDIT,
    SETUP_CREDIT_CODE,
    SETUP_CREDIT_WINDOW,
    SETUP_PRICE,
    THIN_ACTIVE_DAYS,
    THIN_HUMAN_MESSAGES,
)
from slack_audit_digest.lookback import iso_date
from slack_audit_digest.models import AnalysisResult, Intake
from slack_audit_digest.sanitize import assert_no_em_dashes, sanitize_copy

H2_ORDER = [
    "Scope",
    "What we looked for",
    "Top opportunities (ranked)",
    "Suggested specialist seats",
    "What not to automate yet",
    "Optional next step",
]


def render_draft(intake: Intake, result: AnalysisResult) -> str:
    who = intake.name
    if intake.company:
        who = f"{intake.name}, {intake.company}"

    channels = _channel_line(intake, result)
    window = _window_line(result)
    area = intake.area or "the named messy area"

    lines: list[str] = [
        "# Slack Opportunity Audit",
        "",
        f"Prepared for: {who}",
        f"Email: {intake.email}",
        f"Area: {area}",
        f"SKU: Slack Opportunity Audit ({AUDIT_PRICE} one-time)",
        "",
        "This pack is architecture and opportunities only. It does not include prompt packs "
        "or a Command Desk install kit.",
        "",
        "## Scope",
        "",
        f"Channels in scope: {channels}.",
        f"Time window: {window}.",
        (
            f"Human messages in window: {len(result.human_messages)} "
            f"across {result.distinct_active_days} distinct active days."
        ),
    ]
    if result.path == "extended":
        lines.append(
            f"The first {DEFAULT_LOOKBACK_DAYS}-day cut was thin (under about "
            f"{THIN_HUMAN_MESSAGES} human messages or {THIN_ACTIVE_DAYS} active days), "
            f"so we extended toward {MAX_LOOKBACK_DAYS} days. That extended window is what this pack uses."
        )
    elif result.path == "insufficient":
        lines.append(
            f"Volume stayed thin even after the lookback rules (cap {MAX_LOOKBACK_DAYS} days). "
            "This is an insufficient-history pack, not a ranked audit."
        )
    else:
        lines.append(
            f"This is the standard {result.window_days}-day lookback from the newest message in the export."
        )
    if intake.workspace:
        lines.append(f"Workspace notes from intake: {sanitize_copy(intake.workspace)}")
    if intake.notes:
        lines.append(f"Intake notes: {sanitize_copy(intake.notes)}")

    lines += [
        "",
        "## What we looked for",
        "",
        "We read the scoped Slack history for four patterns:",
        "• Repeats: the same question or request showing up again across days.",
        "• Handoffs: @mentions, 'can you take this', and cross-channel pointers that bounce ownership.",
        "• FAQ loops: how-to asks that a macro could draft.",
        "• Status theater: standup-style updates and status pings with no decision attached.",
        "We do not claim hours saved. We only rank what actually showed up in this window.",
        "",
        "## Top opportunities (ranked)",
        "",
    ]

    if result.path == "insufficient":
        lines += _insufficient_opportunities(intake, result)
    elif not result.opportunities:
        lines.append(
            "Volume was enough to look, but we did not find a cluster that met the evidence bar "
            f"(at least 3 related human messages across 2 days). Treat this as a light read of {area}, "
            "not a ranked list."
        )
    else:
        for opp in result.opportunities:
            lines += [
                f"### {opp.rank}. {opp.title}",
                "",
                f"Trigger: {opp.trigger}",
                f"Bot role: {opp.bot_role}",
                f"Keep-human gate: {opp.keep_human_gate}",
            ]
            if opp.example:
                lines.append(f"Example from the window: \"{opp.example}\"")
            lines.append("")

    lines += [
        "## Suggested specialist seats",
        "",
        "Roles only. No prompt text in this pack. Prompts stay with Command Desk Setup if you go that way.",
        "",
    ]
    for seat in result.seats:
        lines.append(f"• {sanitize_copy(seat)}")
    if result.path != "insufficient":
        lines.append(
            "• Human lead (already on the team): keeps sends, exceptions, and customer promises."
        )

    lines += [
        "",
        "## What not to automate yet",
        "",
    ]
    if result.path == "insufficient":
        lines.append("Until history is thicker, do not automate this area. Capture first.")
        lines.append("")
        for item in result.capture_next:
            lines.append(f"• {sanitize_copy(item)}")
        for item in result.do_not_automate:
            lines.append(f"• {sanitize_copy(item)}")
    else:
        for item in result.do_not_automate:
            lines.append(f"• {sanitize_copy(item)}")

    lines += [
        "",
        "## Optional next step",
        "",
        _next_step_body(intake, result),
        "",
        "Tin Dog Digital. Slack Opportunity Audit. Soft CTA only. No ROI guarantee.",
        "",
    ]

    text = "\n".join(lines)
    text = sanitize_copy(text)
    # sanitize_copy is line-agnostic; re-join already clean. Check dashes.
    assert_no_em_dashes(text, "opportunity-draft.md")
    for heading in H2_ORDER:
        marker = f"## {heading}"
        if marker not in text:
            raise RuntimeError(f"draft missing required H2: {heading}")
    return text if text.endswith("\n") else text + "\n"


def _channel_line(intake: Intake, result: AnalysisResult) -> str:
    names = intake.channels or list(result.channel_counts.keys())
    if not names:
        return "(no channel names on intake; used export folder names)"
    return ", ".join(f"#{n.lstrip('#')}" for n in names)


def _window_line(result: AnalysisResult) -> str:
    start = iso_date(result.window_start_ts)
    end = iso_date(result.window_end_ts)
    label = {
        "rich": f"{result.window_days}-day window (standard lookback)",
        "extended": f"{result.window_days}-day window (extended from a thin {DEFAULT_LOOKBACK_DAYS}-day cut)",
        "insufficient": f"{result.window_days}-day window (insufficient history)",
    }[result.path]
    return f"{start} to {end} UTC, {label}"


def _insufficient_opportunities(intake: Intake, result: AnalysisResult) -> list[str]:
    area = intake.area or "the named area"
    return [
        "We are not ranking opportunities from this export.",
        "",
        (
            f"History and volume for {area} were too thin to trust a ranked list. "
            f"We counted {len(result.human_messages)} human messages across "
            f"{result.distinct_active_days} distinct active days in the window we used. "
            f"The bar for a ranked pack is about {THIN_HUMAN_MESSAGES} human messages and "
            f"{THIN_ACTIVE_DAYS} distinct active days, with lookback capped at {MAX_LOOKBACK_DAYS} days."
        ),
        "",
        "That is a valid product outcome, not a failed run. Use the capture list in "
        "'What not to automate yet' and the optional forward-watch if you want a second pass.",
        "",
    ]


def _next_step_body(intake: Intake, result: AnalysisResult) -> str:
    setup = (
        f"Optional next step is Command Desk Setup from this brief (separate {SETUP_PRICE} SKU). "
        f"Code {SETUP_CREDIT_CODE} takes {SETUP_CREDIT} off Setup within {SETUP_CREDIT_WINDOW} "
        "of this audit purchase. Soft offer only. We configure seats and rules from your chat. "
        "Prompts are not in this PDF."
    )
    if result.path == "insufficient":
        if intake.purchased_forward_watch:
            watch = (
                "Forward-watch is already on this order. Use the next two weeks of named-channel "
                "traffic to fill a ranked pack. Do not treat this PDF as the final ranked audit."
            )
        else:
            watch = (
                f"If you want us to watch the named channels going forward, the optional "
                f"{FORWARD_WATCH_PRICE} / {FORWARD_WATCH_DURATION} forward-watch is: {FORWARD_WATCH_URL}"
            )
        return setup + " " + watch
    if intake.purchased_forward_watch:
        return (
            setup
            + " Forward-watch is already on this order. We can fold that traffic into a follow-up if you want it."
        )
    return setup
