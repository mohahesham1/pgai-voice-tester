"""Load configuration from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
PUBLIC_WEBHOOK_URL = os.getenv("PUBLIC_WEBHOOK_URL", "").rstrip("/")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "nova")
OPENAI_STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")

TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER", "+18054398008")

MAX_CALL_DURATION_SECONDS = int(os.getenv("MAX_CALL_DURATION_SECONDS", "180"))
SILENCE_MS_TO_END_TURN = int(os.getenv("SILENCE_MS_TO_END_TURN", "900"))
MIN_SPEECH_MS = int(os.getenv("MIN_SPEECH_MS", "400"))
POST_CALL_DELAY_SECONDS = int(os.getenv("POST_CALL_DELAY_SECONDS", "30"))

RECORDINGS_DIR = ROOT_DIR / "recordings"
TRANSCRIPTS_DIR = ROOT_DIR / "transcripts"
BUG_REPORT_PATH = ROOT_DIR / "bug_report.md"


def validate_for_calling() -> list[str]:
    """Return list of missing/invalid config keys."""
    missing: list[str] = []
    for name, value in [
        ("TWILIO_ACCOUNT_SID", TWILIO_ACCOUNT_SID),
        ("TWILIO_AUTH_TOKEN", TWILIO_AUTH_TOKEN),
        ("TWILIO_PHONE_NUMBER", TWILIO_PHONE_NUMBER),
        ("PUBLIC_WEBHOOK_URL", PUBLIC_WEBHOOK_URL),
        ("OPENAI_API_KEY", OPENAI_API_KEY),
    ]:
        if not value:
            missing.append(name)
    if TARGET_PHONE_NUMBER != "+18054398008":
        missing.append(
            f"TARGET_PHONE_NUMBER must be +18054398008 (got {TARGET_PHONE_NUMBER})"
        )
    return missing
