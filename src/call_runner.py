"""CLI entrypoint: place one test call to the assessment line."""

from __future__ import annotations

import argparse
import sys
import time

from src.config import POST_CALL_DELAY_SECONDS, validate_for_calling
from src.scenarios import list_scenario_ids
from src.twilio_client import place_test_call, wait_for_call_completion


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Place one outbound patient-simulator call to +1-805-439-8008."
    )
    parser.add_argument(
        "--scenario",
        default="schedule_simple",
        choices=list_scenario_ids(),
        help="Patient scenario to simulate",
    )
    parser.add_argument(
        "--label",
        default="",
        help="Call label used for transcript/recording filenames (default: scenario-timestamp)",
    )
    args = parser.parse_args()

    missing = validate_for_calling()
    if missing:
        print("Missing/invalid configuration:", ", ".join(missing), file=sys.stderr)
        print("Copy .env.example to .env and fill in values.", file=sys.stderr)
        return 1

    label = args.label or f"{args.scenario}-{int(time.time())}"
    print(f"Placing call label={label} scenario={args.scenario}")
    call_sid = place_test_call(args.scenario, label)
    print(f"Call SID: {call_sid}")

    status = wait_for_call_completion(call_sid)
    print(f"Call finished with status: {status}")
    print(
        f"Waiting {POST_CALL_DELAY_SECONDS}s for recording/transcript post-processing..."
    )
    time.sleep(POST_CALL_DELAY_SECONDS)
    print(f"Check recordings/{label}.mp3 and transcripts/{label}.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
