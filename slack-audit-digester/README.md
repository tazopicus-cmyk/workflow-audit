# Slack Opportunity Audit digester (F2)

Tin Dog Digital operator tool. After a paid Slack Opportunity Audit ($299) and the post-pay intake, Otto drops named-channel history into a job folder and this CLI writes:

- `opportunity-draft.md` (Ana light-edits)
- `audit-pack.pdf` (client pack)
- `meta.json` (window, counts, path taken)

Offline. No Slack OAuth. No HostGator or Resend deploy. Fixture smoke does not need an API key.

This is not a daily digest product, not an install kit, and not on the Stripe webhook path.

## Install

```bash
cd slack-audit-digester
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

DejaVu fonts are vendored under `fonts/`. If you move the folder, keep `fonts/DejaVuSans.ttf` and `fonts/DejaVuSans-Bold.ttf` next to this README.

## CLI

```bash
# Fixture smoke (no prompts, no API key)
python -m slack_audit_digest run --job fixtures/rich-45d
python -m slack_audit_digest run --job fixtures/thin-history

# Aliases for the brief's sketch
python -m slack_audit_digest run --job jobs/demo-rich
python -m slack_audit_digest run --job jobs/demo-thin

# After Ana edits opportunity-draft.md, rebuild PDF only
python -m slack_audit_digest pdf --job fixtures/rich-45d

# Optional wording enrich (skipped if OPENAI_API_KEY is unset)
python -m slack_audit_digest run --job jobs/acme --llm

# Both fixtures + PDF header + path checks
python -m slack_audit_digest prove
```

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success, including the insufficient-history path (that is a valid product outcome) |
| 1 | `prove` found a contract failure |
| 2 | Missing `intake.json`, missing or empty `slack/`, or invalid input |

`--llm` is optional. Fixtures must pass without it.

## Job layout

```text
jobs/<client-slug>/
  intake.json          # required
  slack/               # required: export for named channels only
  out/                 # written by the CLI
    opportunity-draft.md
    audit-pack.pdf
    meta.json
```

### `intake.json`

Mirrors the live intake form.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | Customer name |
| `email` | string | yes | PDF destination (Ana sends). Echoed in the draft header. |
| `company` | string | no | |
| `area` | string | no | One messy area |
| `channels` | string or string[] | no | Named channels only. Comma-separated string is OK. |
| `workspace` | string | no | Invite notes |
| `notes` | string | no | |
| `sku` | string | no | Default `slack-opportunity-audit` |
| `purchased_forward_watch` | bool | no | If true, copy says watch is already bought |
| `lookback_days_requested` | int | no | Default 45. Capped at 90. |

### Slack export (`slack/`)

No bot token. Accept offline files only:

1. Preferred: Slack workspace export JSON for the scoped channels (`users.json`, `channels.json`, plus `<channel>/<YYYY-MM-DD>.json` daily files with `ts`, `user`, `text`, optional `thread_ts` / `subtype`).
2. Also OK: one JSON array (`.json`) or JSONL (`.jsonl`) per channel. Each object needs `ts` (unix or Slack ts string), `text`, `user` or `user_name`, and `channel` (or the channel is taken from the filename / parent folder).

Bots and system subtypes (`bot_message`, `channel_join`, …) are dropped. Empty text is dropped.

Do not put real customer Slack in this repo. Fixtures are fake.

## Lookback rules (enforced)

1. Default window: last **45 days** from the newest message timestamp in the export.
2. Thin if **fewer than 40 human messages** or **fewer than 10 distinct active days** (UTC date of a human message) inside that window.
3. If thin and older messages exist, extend toward **90 days**. Never unbounded. Cap is 90.
4. If still thin: **insufficient-history** PDF path. Exit 0. Not a crash, not a fake ranked success.

`meta.json` `"path"` is one of:

- `rich`: the requested window (usually 45) had enough volume
- `extended`: 45 was thin, 90 was enough
- `insufficient`: still thin after the cap

## PDF pack (locked H2 order)

1. Scope
2. What we looked for
3. Top opportunities (ranked), each with Trigger / Bot role / Keep-human gate
4. Suggested specialist seats (roles only, no prompt packs)
5. What not to automate yet
6. Optional next step (Command Desk Setup + code `AUDIT150` for $150 off within 30 days of audit purchase). Soft CTA only.

Insufficient path uses the same shell. Section 3 explains the thin window. Sections 5-6 say what to capture next. Optional $99 / 2-week forward-watch is included as plain URL text when it was not already purchased:

`https://buy.stripe.com/cNibJ1f2VeUW4VD7TPdAk0g`

Client-facing copy uses periods, commas, and parentheses. No em dashes. No ROI or hours-saved claims.

## Otto runbook (real paid job)

After Ana has the channel invite (pay and intake already happened on the live funnel; this tool is not on that path):

1. Create `jobs/<client-slug>/intake.json` from the Resend intake email / saved inbox row.
2. Export or copy history for **named channels only** into `jobs/<client-slug>/slack/`. Do not export the whole workspace if they named two channels.
3. Run `python -m slack_audit_digest run --job jobs/<client-slug>`.
4. Ana light-edits `out/opportunity-draft.md`. Rebuild with `python -m slack_audit_digest pdf --job jobs/<client-slug>` if needed.
5. Ana emails `audit-pack.pdf` to the customer. Ops tracks SLA.
6. If `meta.json` path is `insufficient`: send that PDF. Offer the $99 forward-watch if it was not already purchased.

Do not wake Grok Bot or Cursor to produce the PDF. This CLI is the production path for Otto.

## Fixtures

| Path | Expected `meta.json` path | What it proves |
|------|---------------------------|----------------|
| `fixtures/rich-45d/` | `rich` | ≥3 ranked opportunities, full PDF outline |
| `fixtures/thin-history/` | `insufficient` | Thin volume, older messages trigger a 90-day extend, still insufficient, exit 0 |

Regenerate fake Slack (never commit real exports):

```bash
python fixtures/build_fixtures.py
```

## Out of scope (F2)

- Slack OAuth / Events API / live pull
- HostGator upload or Resend send
- Changing the live landing, intake PHP, or Stripe links
- Forward-watch collector automation
- Multi-area audits in one job
