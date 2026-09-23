"""CLI: run a job directory, rebuild PDF from draft, prove fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slack_audit_digest.analyze import analyze
from slack_audit_digest.constants import (
    DEFAULT_LOOKBACK_DAYS,
    MAX_LOOKBACK_DAYS,
    THIN_ACTIVE_DAYS,
    THIN_HUMAN_MESSAGES,
)
from slack_audit_digest.draft import H2_ORDER, render_draft
from slack_audit_digest.ingest import load_intake, load_slack_export
from slack_audit_digest.lookback import iso
from slack_audit_digest.models import AnalysisResult, Intake
from slack_audit_digest.pdf import render_pdf
from slack_audit_digest.sanitize import assert_no_em_dashes

JOB_ALIASES = {
    "demo-rich": "fixtures/rich-45d",
    "demo-thin": "fixtures/thin-history",
    "jobs/demo-rich": "fixtures/rich-45d",
    "jobs/demo-thin": "fixtures/thin-history",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="slack-audit-digest",
        description="Tin Dog Digital Slack Opportunity Audit digester (offline).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Parse intake + slack export, write draft, PDF, meta.")
    run_p.add_argument("--job", required=True, help="Job directory with intake.json and slack/")
    run_p.add_argument("--llm", action="store_true", help="Optional wording enrich (needs OPENAI_API_KEY)")
    run_p.add_argument("--out", default=None, help="Output directory (default: \u003cjob\u003e/out)")

    pdf_p = sub.add_parser("pdf", help="Rebuild audit-pack.pdf from opportunity-draft.md")
    pdf_p.add_argument("--job", required=True)
    pdf_p.add_argument("--out", default=None)

    prove_p = sub.add_parser("prove", help="Run both fixtures and check path, PDF, copy constraints")
    prove_p.add_argument("--root", default=None, help="Package root (default: parent of src/)")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "run":
            return cmd_run(args.job, args.out, args.llm)
        if args.cmd == "pdf":
            return cmd_pdf(args.job, args.out)
        if args.cmd == "prove":
            return cmd_prove(args.root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def resolve_job(job: str) -> Path:
    raw = job.strip()
    mapped = JOB_ALIASES.get(raw) or JOB_ALIASES.get(raw.rstrip("/"))
    path = Path(mapped or raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def cmd_run(job: str, out: str | None, llm: bool) -> int:
    job_dir = resolve_job(job)
    intake_path = job_dir / "intake.json"
    slack_dir = job_dir / "slack"
    if not intake_path.is_file():
        raise FileNotFoundError(f"missing intake.json under {job_dir}")
    if not slack_dir.is_dir():
        raise FileNotFoundError(f"missing slack/ directory under {job_dir}")

    intake = load_intake(intake_path)
    messages = load_slack_export(slack_dir)
    result = analyze(intake, messages, llm_enrich=llm)
    if llm:
        from slack_audit_digest.llm import enrich

        result = enrich(result)

    out_dir = Path(out).resolve() if out else job_dir / "out"
    write_outputs(out_dir, intake, result)
    print(
        f"wrote {out_dir / 'opportunity-draft.md'}\n"
        f"wrote {out_dir / 'audit-pack.pdf'}\n"
        f"wrote {out_dir / 'meta.json'} path={result.path} "
        f"window_days={result.window_days} opportunities={len(result.opportunities)}"
    )
    return 0


def cmd_pdf(job: str, out: str | None) -> int:
    job_dir = resolve_job(job)
    out_dir = Path(out).resolve() if out else job_dir / "out"
    draft_path = out_dir / "opportunity-draft.md"
    if not draft_path.is_file():
        # also accept draft sitting next to intake (Ana moved it)
        alt = job_dir / "opportunity-draft.md"
        if alt.is_file():
            draft_path = alt
        else:
            raise FileNotFoundError(f"missing opportunity-draft.md at {out_dir} or {job_dir}")
    markdown = draft_path.read_text(encoding="utf-8")
    assert_no_em_dashes(markdown, str(draft_path))
    pdf_path = out_dir / "audit-pack.pdf"
    render_pdf(markdown, pdf_path)
    print(f"wrote {pdf_path} ({pdf_path.stat().st_size} bytes)")
    return 0


def write_outputs(out_dir: Path, intake: Intake, result: AnalysisResult) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    draft = render_draft(intake, result)
    (out_dir / "opportunity-draft.md").write_text(draft, encoding="utf-8")
    render_pdf(draft, out_dir / "audit-pack.pdf")
    meta = {
        "path": result.path,
        "window_days": result.window_days,
        "lookback_days_requested": result.lookback_days_requested,
        "newest_message_ts": result.newest_ts,
        "newest_message_at": iso(result.newest_ts),
        "window_start_ts": result.window_start_ts,
        "window_start_at": iso(result.window_start_ts),
        "window_end_ts": result.window_end_ts,
        "window_end_at": iso(result.window_end_ts),
        "human_message_count": len(result.human_messages),
        "distinct_active_days": result.distinct_active_days,
        "channel_counts": result.channel_counts,
        "opportunity_count": len(result.opportunities),
        "opportunities": [o.title for o in result.opportunities],
        "seats": result.seats,
        "extended_from_thin": result.extended_from_thin,
        "llm_enrich": result.llm_enrich,
        "sku": intake.sku,
        "thresholds": {
            "min_human_messages": THIN_HUMAN_MESSAGES,
            "min_active_days": THIN_ACTIVE_DAYS,
            "default_lookback_days": DEFAULT_LOOKBACK_DAYS,
            "max_lookback_days": MAX_LOOKBACK_DAYS,
        },
        "h2_sections": H2_ORDER,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def cmd_prove(root: str | None) -> int:
    pkg = Path(root).resolve() if root else Path(__file__).resolve().parents[2]
    fixtures = [
        (pkg / "fixtures" / "rich-45d", "rich", 3),
        (pkg / "fixtures" / "thin-history", "insufficient", 0),
    ]
    failures: list[str] = []
    for job_dir, expected_path, min_opps in fixtures:
        print(f"\n== prove {job_dir.name} ==")
        try:
            intake = load_intake(job_dir / "intake.json")
            messages = load_slack_export(job_dir / "slack")
            result = analyze(intake, messages)
            out_dir = job_dir / "out"
            write_outputs(out_dir, intake, result)
            draft = (out_dir / "opportunity-draft.md").read_text(encoding="utf-8")
            assert_no_em_dashes(draft, f"{job_dir.name} draft")
            pdf = out_dir / "audit-pack.pdf"
            raw = pdf.read_bytes()
            if not raw.startswith(b"%PDF-"):
                failures.append(f"{job_dir.name}: PDF did not open (%PDF- missing)")
            meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
            if meta["path"] != expected_path:
                failures.append(
                    f"{job_dir.name}: expected path={expected_path} got {meta['path']}"
                )
            if expected_path in {"rich", "extended"} and meta["opportunity_count"] < min_opps:
                failures.append(
                    f"{job_dir.name}: expected >= {min_opps} opportunities, got {meta['opportunity_count']}"
                )
            if expected_path == "insufficient" and meta["opportunity_count"] != 0:
                failures.append(f"{job_dir.name}: insufficient path should not rank opportunities")
            for heading in H2_ORDER:
                if f"## {heading}" not in draft:
                    failures.append(f"{job_dir.name}: missing H2 {heading}")
            if expected_path == "insufficient":
                lower = draft.lower()
                if "thin" not in lower and "insufficient" not in lower:
                    failures.append(f"{job_dir.name}: insufficient draft does not explain thin history")
                if "buy.stripe.com" not in draft and "forward-watch" not in lower:
                    failures.append(f"{job_dir.name}: insufficient draft missing forward-watch mention")
            print(
                f"ok {job_dir.name} path={meta['path']} "
                f"msgs={meta['human_message_count']} days={meta['distinct_active_days']} "
                f"opps={meta['opportunity_count']} pdf={pdf.stat().st_size}B"
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{job_dir.name}: {type(exc).__name__}: {exc}")
            print(f"FAIL {job_dir.name}: {exc}")
    if failures:
        print("\nprove failed:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("\nprove passed: rich + thin fixtures, PDFs open, meta.json paths correct.")
    return 0
