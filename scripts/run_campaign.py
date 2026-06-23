"""Run a batch of scenario calls (minimum 10 for submission)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import POST_CALL_DELAY_SECONDS, validate_for_calling
from src.scenarios import list_scenario_ids
from src.twilio_client import place_test_call, wait_for_call_completion

DEFAULT_CAMPAIGN = [
    "schedule_simple",
    "reschedule",
    "cancel",
    "medication_refill",
    "office_hours",
    "location_insurance",
    "vague_request",
    "topic_change",
    "sunday_edge",
    "interruption",
    "wrong_info_correction",
    "multi_request",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run multiple assessment calls.")
    parser.add_argument(
        "--scenarios",
        nargs="*",
        default=DEFAULT_CAMPAIGN,
        help="Scenario IDs to run in order",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=POST_CALL_DELAY_SECONDS,
        help="Seconds between calls",
    )
    args = parser.parse_args()

    missing = validate_for_calling()
    if missing:
        print("Missing/invalid configuration:", ", ".join(missing), file=sys.stderr)
        return 1

    unknown = [s for s in args.scenarios if s not in list_scenario_ids()]
    if unknown:
        print("Unknown scenarios:", ", ".join(unknown), file=sys.stderr)
        return 1

    if len(args.scenarios) < 10:
        print("Warning: submission requires at least 10 calls.", file=sys.stderr)

    print("IMPORTANT: Start the webhook server first:")
    print("  python -m uvicorn src.server:app --host 0.0.0.0 --port 8080")
    print("And expose it with ngrok:")
    print("  ngrok http 8080")
    print()

    for idx, scenario_id in enumerate(args.scenarios, start=1):
        label = f"call-{idx:02d}-{scenario_id}"
        print(f"[{idx}/{len(args.scenarios)}] Calling scenario={scenario_id} label={label}")
        call_sid = place_test_call(scenario_id, label)
        status = wait_for_call_completion(call_sid)
        print(f"  status={status} sid={call_sid}")
        if idx < len(args.scenarios):
            time.sleep(args.delay)

    print("Campaign complete. Review recordings/, transcripts/, and bug_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
