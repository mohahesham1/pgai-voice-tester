"""Post-call quality analysis for Athena agent responses."""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from src.config import BUG_REPORT_PATH, OPENAI_API_KEY, OPENAI_MODEL


ANALYSIS_PROMPT = """You are a QA engineer reviewing phone agent transcripts for a medical office AI.

Identify concrete bugs or quality issues in the AGENT's behavior (not the patient simulator).
Focus on:
- Incorrect scheduling (e.g., weekends/holidays not validated)
- Wrong policy/info (insurance, hours, location)
- Failure to clarify ambiguous requests
- Unsafe medical advice
- Poor conversational flow or ignoring user corrections

Return JSON array. Each item:
{
  "title": "short bug title",
  "severity": "High|Medium|Low",
  "timestamp_hint": "approx location in transcript",
  "details": "what happened",
  "why_it_matters": "patient impact",
  "expected_behavior": "what should have happened"
}

If no meaningful issues, return [].
"""


def analyze_transcript_text(transcript_text: str, call_label: str) -> list[dict]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Call label: {call_label}\n\n"
                    f"Transcript:\n{transcript_text}\n\n"
                    'Respond as {"issues": [...]}'
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    issues = data.get("issues", data if isinstance(data, list) else [])
    return issues if isinstance(issues, list) else []


def append_issues_to_bug_report(
    call_label: str,
    transcript_path: Path,
    recording_path: Path | None,
    issues: list[dict],
) -> None:
    if not issues:
        return

    BUG_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not BUG_REPORT_PATH.exists():
        BUG_REPORT_PATH.write_text(
            "# Bug Report — Pretty Good AI Voice Assessment\n\n"
            "Issues found while testing +1-805-439-8008.\n\n",
            encoding="utf-8",
        )

    chunks: list[str] = []
    for issue in issues:
        rec = recording_path.name if recording_path else "n/a"
        chunks.append(
            f"## Bug: {issue.get('title', 'Untitled')}\n"
            f"- **Severity:** {issue.get('severity', 'Medium')}\n"
            f"- **Call:** {transcript_path.name} ({call_label}), {issue.get('timestamp_hint', 'n/a')}\n"
            f"- **Recording:** {rec}\n"
            f"- **Details:** {issue.get('details', '')}\n"
            f"- **Why it matters:** {issue.get('why_it_matters', '')}\n"
            f"- **Expected:** {issue.get('expected_behavior', '')}\n"
        )

    with BUG_REPORT_PATH.open("a", encoding="utf-8") as f:
        f.write("\n".join(chunks) + "\n")
