"""Deterministic Slack opportunity heuristics. No API required."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from slack_audit_digest.constants import (
    MAX_OPPORTUNITIES,
    MIN_CLUSTER_DAYS,
    MIN_CLUSTER_MESSAGES,
)
from slack_audit_digest.lookback import apply_lookback, distinct_days
from slack_audit_digest.models import AnalysisResult, Cluster, Intake, Message, Opportunity
from slack_audit_digest.sanitize import sanitize_copy

_URL = re.compile(r"<https?://[^>]+>|https?://\S+")
_MENTION = re.compile(r"<@[\w]+(\|[^>]+)?>|<#([\w-]+)(\|[^>]+)?>")
_EMOJI = re.compile(r":[a-z0-9_+-]+:")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")

STOP = frozenset(
    """
    a an the and or but if to of in on for at by from with as is are was were be been
    i we you they it this that these those just please hey hi hello thanks thank yeah
    ok okay still also our your my their not no yes do did does can could would should
    about into over out up so than then there here what when who whom how why where which
    order ticket customer tickets orders
    """.split()
)

HANDOFF_RE = re.compile(
    r"\b(can you take|could you take|taking this|handing (this )?off|hand[- ]off|"
    r"over to you|looping in|can someone (grab|take)|passing this|routing this|"
    r"moving this to|please take)\b",
    re.I,
)
PING_RE = re.compile(
    r"\b(any update|status on|still waiting|checking in|following up|follow up|"
    r"bump(ing)? this|ping on|heard back)\b",
    re.I,
)
THEATER_RE = re.compile(
    r"\b(standup|stand-up|stand up|yesterday i|today i('ll| will| am)?|"
    r"no blockers?|working on|eod update|eod:)\b",
    re.I,
)
APPROVAL_RE = re.compile(
    r"\b(sign[- ]off|approve|approval|can i proceed|green light|need a yes|"
    r"ok to send|okay to send|need (you to )?sign)\b",
    re.I,
)
QUESTION_RE = re.compile(
    r"\?|\b(how do i|how can|how do we|where is|where'?s|what'?s the|"
    r"what is the|can we refund|do we (still )?offer)\b",
    re.I,
)
ANGRY_RE = re.compile(
    r"\b(furious|lawsuit|attorney|lawyer|angry|unacceptable|chargeback|"
    r"better business bureau|bbb complaint)\b",
    re.I,
)

KIND_SEATS = {
    "faq": "FAQ Drafter",
    "handoff": "Handoff Coordinator",
    "status_ping": "Ticket Tracker",
    "status_theater": "Status Digest",
    "approval": "Approval Clerk",
}

KIND_TITLES = {
    "faq": "Repeat questions that a drafter can answer from macros",
    "handoff": "Bouncing handoffs that stall before an owner is clear",
    "status_ping": "Status pings that ask the same ticket question again",
    "status_theater": "Standup-style updates with no decision attached",
    "approval": "Approval waits that sit in Slack until someone says yes",
}

# First-pass FAQ buckets. Real jobs still use greedy overlap for leftovers.
FAQ_TOPIC_SEEDS: list[tuple[str, tuple[str, ...]]] = [
    ("refund", ("refund", "refunds")),
    ("shipping", ("shipping", "tracking", "delivery", "package")),
    ("login", ("password", "login", "logged", "locked")),
    ("invoice", ("invoice", "invoices", "billing", "receipt")),
    ("warranty", ("warranty", "warranties")),
    ("cancel", ("cancel", "cancellation", "canceled", "cancelled")),
]


def analyze(intake: Intake, messages: list[Message], llm_enrich: bool = False) -> AnalysisResult:
    path, window_days, newest, start, end, humans, all_in, extended = apply_lookback(
        messages, intake.lookback_days_requested
    )
    if intake.channels:
        wanted = {_norm_chan(c) for c in intake.channels}
        # Keep unmatched exports too if named channels are a subset; prefer named.
        scoped_h = [m for m in humans if _norm_chan(m.channel) in wanted]
        scoped_all = [m for m in all_in if _norm_chan(m.channel) in wanted]
        if scoped_h:
            humans = scoped_h
            all_in = scoped_all

    channel_counts: dict[str, int] = {}
    for m in humans:
        channel_counts[m.channel] = channel_counts.get(m.channel, 0) + 1

    opportunities: list[Opportunity] = []
    seats: list[str] = []
    do_not: list[str] = []
    capture: list[str] = []
    notes: list[str] = []

    if path == "insufficient":
        capture = _capture_next(intake, humans)
        do_not = [
            "Do not invent ranked opportunities from a thin sample.",
            "Do not auto-reply, auto-assign, or auto-send until a fuller window exists.",
            "Keep any customer promise, refund exception, or angry thread with a person.",
        ]
        seats = [
            "Too early to name specialist seats from this window. Capture the traffic below first.",
        ]
        notes.append("insufficient-history path")
    else:
        clusters = _build_clusters(humans)
        opportunities = _clusters_to_opportunities(clusters)
        seats = _seats_from(opportunities, humans)
        do_not = _do_not_automate(humans, opportunities)
        capture = []
        notes.append(f"clusters={len(clusters)} opportunities={len(opportunities)}")

    return AnalysisResult(
        path=path,
        window_days=window_days,
        lookback_days_requested=intake.lookback_days_requested,
        newest_ts=newest,
        window_start_ts=start,
        window_end_ts=end,
        human_messages=humans,
        all_in_window=all_in,
        distinct_active_days=distinct_days(humans),
        channel_counts=channel_counts,
        opportunities=opportunities,
        seats=seats,
        do_not_automate=do_not,
        capture_next=capture,
        notes_internal=notes,
        extended_from_thin=extended,
        llm_enrich=llm_enrich,
    )


def _norm_chan(name: str) -> str:
    return name.strip().lstrip("#").lower()


def normalize_text(text: str) -> str:
    t = text.lower()
    t = _MENTION.sub(" ", t)
    t = _URL.sub(" ", t)
    t = _EMOJI.sub(" ", t)
    t = _NON_ALNUM.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def content_tokens(norm: str) -> list[str]:
    return [tok for tok in norm.split() if tok not in STOP and len(tok) > 2]


def classify(text: str) -> str:
    if HANDOFF_RE.search(text):
        return "handoff"
    if THEATER_RE.search(text) and not QUESTION_RE.search(text):
        return "status_theater"
    if PING_RE.search(text):
        return "status_ping"
    if APPROVAL_RE.search(text):
        return "approval"
    if QUESTION_RE.search(text):
        return "faq"
    return "other"


def _build_clusters(humans: list[Message]) -> list[Cluster]:
    by_kind: dict[str, list[Message]] = defaultdict(list)
    for m in humans:
        kind = classify(m.text)
        if kind != "other":
            by_kind[kind].append(m)

    clusters: list[Cluster] = []

    # Pattern kinds (except faq) are one cluster each if they meet volume.
    for kind in ("handoff", "status_ping", "status_theater", "approval"):
        msgs = by_kind.get(kind) or []
        if _eligible(msgs):
            clusters.append(
                Cluster(
                    key=kind,
                    kind=kind,
                    title_hint=KIND_TITLES[kind],
                    messages=msgs,
                    topic_terms=_top_terms(msgs, 5),
                )
            )

    faq_msgs = by_kind.get("faq") or []
    for sub, seed in _faq_buckets(faq_msgs):
        if _eligible(sub):
            terms = _top_terms(sub, 4)
            if seed and seed not in terms:
                terms = [seed] + [t for t in terms if t != seed]
            hint = "Repeat questions about " + (", ".join(terms[:3]) if terms else "the same topic")
            clusters.append(
                Cluster(
                    key="faq:" + "-".join(terms[:3] or ["general"]),
                    kind="faq",
                    title_hint=hint,
                    messages=sub,
                    topic_terms=terms,
                )
            )

    clusters.sort(key=lambda c: (-c.score, -c.count, c.key))
    return clusters


def _eligible(msgs: list[Message]) -> bool:
    if len(msgs) < MIN_CLUSTER_MESSAGES:
        return False
    days = {m.day for m in msgs}
    return len(days) >= MIN_CLUSTER_DAYS


def _faq_buckets(messages: list[Message]) -> list[tuple[list[Message], str | None]]:
    remaining = list(messages)
    buckets: list[tuple[list[Message], str | None]] = []
    for seed, aliases in FAQ_TOPIC_SEEDS:
        hit: list[Message] = []
        keep: list[Message] = []
        for m in remaining:
            norm = normalize_text(m.text)
            toks = set(content_tokens(norm))
            if seed in toks or any(alias in toks or alias in norm for alias in aliases):
                hit.append(m)
            else:
                keep.append(m)
        if hit:
            buckets.append((hit, seed))
        remaining = keep
    for group in _greedy_token_clusters(remaining):
        buckets.append((group, None))
    return buckets


def _greedy_token_clusters(messages: list[Message], threshold: float = 0.28) -> list[list[Message]]:
    if not messages:
        return []
    items = [(m, set(content_tokens(normalize_text(m.text)))) for m in messages]
    used = [False] * len(items)
    groups: list[list[Message]] = []
    for i, (msg_i, toks_i) in enumerate(items):
        if used[i] or not toks_i:
            continue
        group = [msg_i]
        used[i] = True
        centroid = set(toks_i)
        changed = True
        while changed:
            changed = False
            for j, (msg_j, toks_j) in enumerate(items):
                if used[j] or not toks_j:
                    continue
                if _jaccard(centroid, toks_j) >= threshold:
                    used[j] = True
                    group.append(msg_j)
                    centroid |= toks_j
                    changed = True
        groups.append(group)
    groups.sort(key=lambda g: -len(g))
    return groups


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _top_terms(messages: list[Message], n: int) -> list[str]:
    counts: Counter[str] = Counter()
    for m in messages:
        counts.update(content_tokens(normalize_text(m.text)))
    return [term for term, _ in counts.most_common(n)]


def _example(messages: list[Message]) -> str:
    best = max(messages, key=lambda m: (len(m.text), -m.ts))
    text = re.sub(r"<@[\w]+(\|[^>]+)?>", "@teammate", best.text)
    text = re.sub(r"<#[\w-]+(\|[^>]+)?>", "#channel", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 180:
        text = text[:177] + "..."
    return sanitize_copy(text)


def _clusters_to_opportunities(clusters: list[Cluster]) -> list[Opportunity]:
    out: list[Opportunity] = []
    for i, cluster in enumerate(clusters[:MAX_OPPORTUNITIES], start=1):
        out.append(_opportunity_from_cluster(i, cluster))
    return out


def _opportunity_from_cluster(rank: int, cluster: Cluster) -> Opportunity:
    chans = cluster.channels
    chan_txt = ", ".join(f"#{c}" for c in chans) or "the scoped channels"
    terms = cluster.topic_terms
    topic = ", ".join(terms[:3]) if terms else "this topic"
    example = _example(cluster.messages)
    role = KIND_SEATS[cluster.kind]
    title = sanitize_copy(_title_for(cluster, topic))
    trigger, bot_role, gate = _copy_for(cluster.kind, chan_txt, topic, cluster, role)
    return Opportunity(
        rank=rank,
        title=title,
        trigger=sanitize_copy(trigger),
        bot_role=sanitize_copy(bot_role),
        keep_human_gate=sanitize_copy(gate),
        kind=cluster.kind,
        evidence_count=cluster.count,
        evidence_days=len(cluster.days),
        channels=chans,
        example=example,
    )


def _title_for(cluster: Cluster, topic: str) -> str:
    if cluster.kind == "faq":
        head = cluster.topic_terms[0] if cluster.topic_terms else "repeat"
        return f"Repeat {head} questions that a FAQ drafter can handle"
    return KIND_TITLES[cluster.kind]


def _copy_for(
    kind: str, chan_txt: str, topic: str, cluster: Cluster, role: str
) -> tuple[str, str, str]:
    n = cluster.count
    d = len(cluster.days)
    if kind == "faq":
        trigger = (
            f"The same {topic} questions keep showing up in {chan_txt} "
            f"({n} human messages across {d} days)."
        )
        bot = (
            f"{role} would match the ask to a known macro, drop a draft in the thread, "
            "and tag the thread as FAQ vs unique."
        )
        gate = (
            "A person still sends the reply, handles exceptions (policy, dollar amount, "
            "angry tone), and edits anything that would bind the company."
        )
    elif kind == "handoff":
        trigger = (
            f"Requests bounce with @mentions and 'can you take this' language in {chan_txt} "
            f"({n} messages across {d} days)."
        )
        bot = (
            f"{role} would capture the thread summary, route it to the named queue, "
            "and record who owns it so the ping does not restart."
        )
        gate = (
            "A person still accepts ownership, talks to the customer on messy cases, "
            "and makes any promise about timing or make-goods."
        )
    elif kind == "status_ping":
        trigger = (
            f"People re-ask for ticket or order status in {chan_txt} "
            f"({n} pings across {d} days) instead of reading a system of record."
        )
        bot = (
            f"{role} would look up the last known status and post it in-thread, "
            "then mark the ping as answered or blocked."
        )
        gate = (
            "A person still owns a missed SLA, a slipped ETA, or any case with no record. "
            "The bot does not invent a status."
        )
    elif kind == "status_theater":
        trigger = (
            f"Standup-style updates land in {chan_txt} "
            f"({n} messages across {d} days) with little or no decision."
        )
        bot = (
            f"{role} would collect yesterday / today / blocker lines into one digest "
            "and flag only the blockers that need a human call."
        )
        gate = (
            "Priority calls, customer commitments, and anything that changes the queue "
            "stay with a lead. The digest is a rollup, not a decision."
        )
    else:  # approval
        trigger = (
            f"Work waits on a yes/no in {chan_txt} "
            f"({n} approval-shaped messages across {d} days)."
        )
        bot = (
            f"{role} would assemble the packet (link, ask, deadline), remind the named "
            "approver, and log the decision once a person answers."
        )
        gate = (
            "The actual yes or no stays human. Refunds, legal, and public replies "
            "never auto-approve."
        )
    return trigger, bot, gate


def _seats_from(opportunities: list[Opportunity], humans: list[Message]) -> list[str]:
    seats: list[str] = []
    for opp in opportunities:
        if opp.bot_role.split(" ")[0:2]:
            role = opp.bot_role.split(" would")[0].strip()
            if role and role not in seats:
                seats.append(role)
    # Always keep a human escalation seat when handoffs or anger show up.
    if any(o.kind == "handoff" for o in opportunities) or any(ANGRY_RE.search(m.text) for m in humans):
        if "Escalation Owner" not in seats:
            seats.append("Escalation Owner")
    if "Knowledge Curator" not in seats and any(o.kind == "faq" for o in opportunities):
        seats.append("Knowledge Curator")
    return seats


def _do_not_automate(humans: list[Message], opportunities: list[Opportunity]) -> list[str]:
    items = [
        "Do not auto-send customer replies. Drafts only, until a later desk install proves otherwise.",
        "Do not let a bot make refund, legal, or PR promises.",
        "Do not dump full customer histories into tools by default.",
    ]
    if any(ANGRY_RE.search(m.text) for m in humans):
        items.insert(
            0,
            "Angry, legal, or chargeback language showed up. Those threads stay with Escalation Owner.",
        )
    if any(o.kind == "approval" for o in opportunities):
        items.append("Do not auto-approve. Log the request, then wait for a person.")
    if any(o.kind == "status_theater" for o in opportunities):
        items.append("Do not treat standup rollups as a substitute for a lead making priority calls.")
    return items


def _capture_next(intake: Intake, humans: list[Message]) -> list[str]:
    chans = ", ".join(f"#{c}" for c in intake.channels) if intake.channels else "the named channels"
    return [
        f"Keep {chans} exporting (or invite us) so the next two weeks of traffic are in one place.",
        "When a repeat question appears, leave it in-channel rather than DMs so the pattern is visible.",
        "Tag or thread the messy area named on intake so handoffs and FAQ loops are easier to count.",
        "If volume stays low, the optional 2-week forward-watch is the right next capture, not a guessed audit.",
    ]
