"""Optional LLM enrich. Fixtures must pass without this. Behind --llm only."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from slack_audit_digest.models import AnalysisResult
from slack_audit_digest.sanitize import sanitize_copy

_SYSTEM = (
    "You rewrite Slack Opportunity Audit opportunity titles and trigger lines. "
    "Keep facts. No hype. No ROI or hours-saved claims. No prompt packs. "
    "No em dashes. Use periods, commas, parentheses. Return JSON only."
)


def enrich(result: AnalysisResult) -> AnalysisResult:
    """Polish opportunity wording if OPENAI_API_KEY is set. Otherwise no-op."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("note: --llm set but OPENAI_API_KEY is empty. Using deterministic copy.")
        return result
    if result.path == "insufficient" or not result.opportunities:
        return result

    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    [
                        {
                            "rank": o.rank,
                            "title": o.title,
                            "trigger": o.trigger,
                            "bot_role": o.bot_role,
                            "keep_human_gate": o.keep_human_gate,
                        }
                        for o in result.opportunities
                    ]
                )
                + "\nRewrite title and trigger only. Return a JSON array with rank, title, trigger.",
            },
        ],
    }
    req = urllib.request.Request(
        os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        rewritten = json.loads(_strip_fence(content))
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, IndexError) as exc:
        print(f"note: --llm enrich failed ({exc}). Using deterministic copy.")
        return result

    by_rank = {int(item["rank"]): item for item in rewritten if "rank" in item}
    for opp in result.opportunities:
        item = by_rank.get(opp.rank)
        if not item:
            continue
        if item.get("title"):
            opp.title = sanitize_copy(str(item["title"]))
        if item.get("trigger"):
            opp.trigger = sanitize_copy(str(item["trigger"]))
    result.llm_enrich = True
    return result


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()
