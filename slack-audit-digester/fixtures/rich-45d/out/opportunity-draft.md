# Slack Opportunity Audit

Prepared for: Maya Chen, Northline Outfitters
Email: maya@northline.test
Area: customer support
SKU: Slack Opportunity Audit ($299 one-time)

This pack is architecture and opportunities only. It does not include prompt packs or a Command Desk install kit.

## Scope

Channels in scope: #support, #support-escalations.
Time window: 2026-08-08 to 2026-09-22 UTC, 45-day window (standard lookback).
Human messages in window: 87 across 43 distinct active days.
This is the standard 45-day lookback from the newest message in the export.
Workspace notes from intake: Invite was to #support and #support-escalations only.
Intake notes: Wholesale VIP tickets keep slipping. Refund how-to is the loudest loop.

## What we looked for

We read the scoped Slack history for four patterns:
• Repeats: the same question or request showing up again across days.
• Handoffs: @mentions, 'can you take this', and cross-channel pointers that bounce ownership.
• FAQ loops: how-to asks that a macro could draft.
• Status theater: standup-style updates and status pings with no decision attached.
We do not claim hours saved. We only rank what actually showed up in this window.

## Top opportunities (ranked)

### 1. Standup-style updates with no decision attached

Trigger: Standup-style updates land in #support (24 messages across 16 days) with little or no decision.
Bot role: Status Digest would collect yesterday / today / blocker lines into one digest and flag only the blockers that need a human call.
Keep-human gate: Priority calls, customer commitments, and anything that changes the queue stay with a lead. The digest is a rollup, not a decision.
Example from the window: "Standup: yesterday I finished the queue sweep. Today I will draft macros. No blocker besides the lodge order."

### 2. Repeat refund questions that a FAQ drafter can handle

Trigger: The same refund, request, jacket questions keep showing up in #support (13 human messages across 13 days).
Bot role: FAQ Drafter would match the ask to a known macro, drop a draft in the thread, and tag the thread as FAQ vs unique.
Keep-human gate: A person still sends the reply, handles exceptions (policy, dollar amount, angry tone), and edits anything that would bind the company.
Example from the window: "Same refund how-to. Customer wants a refund on order 4408. Do we still offer store credit?"

### 3. Repeat tracking questions that a FAQ drafter can handle

Trigger: The same tracking, shipping, eta questions keep showing up in #support (12 human messages across 12 days).
Bot role: FAQ Drafter would match the ask to a known macro, drop a draft in the thread, and tag the thread as FAQ vs unique.
Keep-human gate: A person still sends the reply, handles exceptions (policy, dollar amount, angry tone), and edits anything that would bind the company.
Example from the window: "Tracking number for order 8807 looks stale. Where is this order supposed to be?"

### 4. Bouncing handoffs that stall before an owner is clear

Trigger: Requests bounce with @mentions and 'can you take this' language in #support-escalations, #support (11 messages across 11 days).
Bot role: Handoff Coordinator would capture the thread summary, route it to the named queue, and record who owns it so the ping does not restart.
Keep-human gate: A person still accepts ownership, talks to the customer on messy cases, and makes any promise about timing or make-goods.
Example from the window: "Over to you @teammate. Handing this off, the customer is repeating themselves."

### 5. Status pings that ask the same ticket question again

Trigger: People re-ask for ticket or order status in #support (10 pings across 10 days) instead of reading a system of record.
Bot role: Ticket Tracker would look up the last known status and post it in-thread, then mark the ping as answered or blocked.
Keep-human gate: A person still owns a missed SLA, a slipped ETA, or any case with no record. The bot does not invent a status.
Example from the window: "Any update on ticket 1204? Sales is still waiting on a ship date."

## Suggested specialist seats

Roles only. No prompt text in this pack. Prompts stay with Command Desk Setup if you go that way.

• Status Digest
• FAQ Drafter
• Handoff Coordinator
• Ticket Tracker
• Escalation Owner
• Knowledge Curator
• Human lead (already on the team): keeps sends, exceptions, and customer promises.

## What not to automate yet

• Angry, legal, or chargeback language showed up. Those threads stay with Escalation Owner.
• Do not auto-send customer replies. Drafts only, until a later desk install proves otherwise.
• Do not let a bot make refund, legal, or PR promises.
• Do not dump full customer histories into tools by default.
• Do not treat standup rollups as a substitute for a lead making priority calls.

## Optional next step

Optional next step is Command Desk Setup from this brief (separate $799 SKU). Code AUDIT150 takes $150 off Setup within 30 days of this audit purchase. Soft offer only. We configure seats and rules from your chat. Prompts are not in this PDF.

Tin Dog Digital. Slack Opportunity Audit. Soft CTA only. No ROI guarantee.
