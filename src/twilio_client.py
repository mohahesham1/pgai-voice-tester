"""Twilio REST helpers for placing calls and fetching recordings."""

from __future__ import annotations

import time
from pathlib import Path

import httpx
from twilio.rest import Client

from src.config import (
    MAX_CALL_DURATION_SECONDS,
    PUBLIC_WEBHOOK_URL,
    RECORDINGS_DIR,
    TARGET_PHONE_NUMBER,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
)


def twilio_client() -> Client:
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def place_test_call(scenario_id: str, call_label: str) -> str:
    """
    Place outbound call to assessment line.
    Returns Twilio Call SID.
    """
    voice_url = (
        f"{PUBLIC_WEBHOOK_URL}/twilio/voice"
        f"?scenario={scenario_id}&label={call_label}"
    )
    status_url = (
        f"{PUBLIC_WEBHOOK_URL}/twilio/status"
        f"?scenario={scenario_id}&label={call_label}"
    )

    call = twilio_client().calls.create(
        to=TARGET_PHONE_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url=voice_url,
        status_callback=status_url,
        status_callback_event=["completed"],
        status_callback_method="POST",
        record=True,
        recording_channels="dual",
        time_limit=MAX_CALL_DURATION_SECONDS,
        machine_detection="Enable",
    )
    return call.sid


def wait_for_call_completion(call_sid: str, poll_seconds: int = 5, timeout: int = 240) -> str:
    """Poll until call completes. Returns final status."""
    client = twilio_client()
    elapsed = 0
    while elapsed < timeout:
        call = client.calls(call_sid).fetch()
        if call.status in {"completed", "busy", "failed", "no-answer", "canceled"}:
            return call.status
        time.sleep(poll_seconds)
        elapsed += poll_seconds
    return "timeout"


def download_call_recording(call_sid: str, output_path: Path) -> Path | None:
    """Download first recording for call as MP3."""
    client = twilio_client()
    recordings = client.recordings.list(call_sid=call_sid, limit=1)
    if not recordings:
        return None

    recording_resource = client.recordings(recordings[0].sid).fetch()
    mp3_url = f"https://api.twilio.com{recording_resource.uri.replace('.json', '.mp3')}"

    response = httpx.get(
        mp3_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=60.0,
    )
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path
