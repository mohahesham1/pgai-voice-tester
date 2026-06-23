"""FastAPI server: Twilio webhooks + bidirectional media stream voice loop."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from openai import OpenAI

from src.analyzer import analyze_transcript_text, append_issues_to_bug_report
from src.audio import (
    decode_mulaw_payload,
    encode_mulaw_payload,
    mp3_to_mulaw_chunks,
    mulaw_energy,
    mulaw_to_wav_bytes,
)
from src.config import (
    MAX_CALL_DURATION_SECONDS,
    MIN_SPEECH_MS,
    OPENAI_API_KEY,
    OPENAI_STT_MODEL,
    OPENAI_TTS_VOICE,
    PUBLIC_WEBHOOK_URL,
    RECORDINGS_DIR,
    SILENCE_MS_TO_END_TURN,
    TRANSCRIPTS_DIR,
)
from src.patient_agent import PatientAgent
from src.scenarios import get_scenario
from src.twilio_client import download_call_recording, twilio_client

logger = logging.getLogger(__name__)
app = FastAPI(title="PGAI Voice Patient Simulator")

# stream_sid -> session
SESSIONS: dict[str, "CallSession"] = {}
# call_sid -> label for post-processing
CALL_LABELS: dict[str, str] = {}


@dataclass
class CallSession:
    scenario_id: str
    label: str
    call_sid: str | None = None
    stream_sid: str | None = None
    patient: PatientAgent | None = None
    audio_buffer: bytearray = field(default_factory=bytearray)
    speech_started_at: float | None = None
    last_voice_at: float | None = None
    processing: bool = False
    ended: bool = False
    started_at: float = field(default_factory=time.time)
    openai: OpenAI = field(default_factory=lambda: OpenAI(api_key=OPENAI_API_KEY))

    def transcript_lines(self) -> list[str]:
        if not self.patient:
            return []
        lines: list[str] = []
        for turn in self.patient.turns:
            speaker = "AGENT" if turn.role == "agent" else "PATIENT"
            lines.append(f"{speaker}: {turn.text}")
        return lines


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "pgai-voice-tester"}


@app.post("/twilio/voice")
async def twilio_voice(request: Request) -> Response:
    scenario_id = request.query_params.get("scenario", "schedule_simple")
    label = request.query_params.get("label", f"call-{int(time.time())}")
    stream_url = PUBLIC_WEBHOOK_URL.replace("https://", "wss://").replace(
        "http://", "ws://"
    )
    stream_url = f"{stream_url}/twilio/media-stream"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{stream_url}">
      <Parameter name="scenario" value="{scenario_id}" />
      <Parameter name="label" value="{label}" />
    </Stream>
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/twilio/status")
async def twilio_status(request: Request) -> dict[str, str]:
    form = await request.form()
    call_sid = str(form.get("CallSid", ""))
    call_status = str(form.get("CallStatus", ""))
    scenario_id = request.query_params.get("scenario", "schedule_simple")
    label = request.query_params.get("label", call_sid)

    if call_sid:
        CALL_LABELS[call_sid] = label

    if call_status == "completed" and call_sid:
        asyncio.create_task(_post_call_pipeline(call_sid, scenario_id, label))
    return {"ok": "true"}


@app.websocket("/twilio/media-stream")
async def media_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    session: CallSession | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            message: dict[str, Any] = json.loads(raw)
            event = message.get("event")

            if event == "start":
                start = message.get("start", {})
                stream_sid = start.get("streamSid")
                call_sid = start.get("callSid")
                params = start.get("customParameters", {})
                scenario_id = params.get("scenario", "schedule_simple")
                label = params.get("label", f"call-{int(time.time())}")

                scenario = get_scenario(scenario_id)
                session = CallSession(
                    scenario_id=scenario_id,
                    label=label,
                    call_sid=call_sid,
                    stream_sid=stream_sid,
                    patient=PatientAgent(scenario=scenario),
                )
                if stream_sid:
                    SESSIONS[stream_sid] = session
                if call_sid:
                    CALL_LABELS[call_sid] = label
                logger.info("Stream started label=%s scenario=%s", label, scenario_id)

            elif event == "media" and session and session.stream_sid:
                payload = message.get("media", {}).get("payload", "")
                if not payload or session.processing or session.ended:
                    continue

                chunk = decode_mulaw_payload(payload)
                energy = mulaw_energy(chunk)
                now = time.time()

                if energy > 450:
                    if session.speech_started_at is None:
                        session.speech_started_at = now
                    session.last_voice_at = now
                    session.audio_buffer.extend(chunk)
                elif session.speech_started_at and session.last_voice_at:
                    silence_ms = (now - session.last_voice_at) * 1000
                    if silence_ms >= SILENCE_MS_TO_END_TURN:
                        speech_ms = (session.last_voice_at - session.speech_started_at) * 1000
                        if speech_ms >= MIN_SPEECH_MS and session.audio_buffer:
                            await _handle_agent_turn(websocket, session)
                        session.audio_buffer.clear()
                        session.speech_started_at = None
                        session.last_voice_at = None

                if (now - session.started_at) > MAX_CALL_DURATION_SECONDS:
                    await _end_call(session)

            elif event == "stop" and session:
                await _save_transcript(session)
                session.ended = True
                if session.stream_sid:
                    SESSIONS.pop(session.stream_sid, None)
                break

    except WebSocketDisconnect:
        if session:
            await _save_transcript(session)
            if session.stream_sid:
                SESSIONS.pop(session.stream_sid, None)


async def _handle_agent_turn(websocket: WebSocket, session: CallSession) -> None:
    if not session.patient or session.processing:
        return

    session.processing = True
    try:
        wav_bytes = mulaw_to_wav_bytes(bytes(session.audio_buffer))
        session.audio_buffer.clear()

        transcript = await asyncio.to_thread(_transcribe_wav, session.openai, wav_bytes)
        transcript = transcript.strip()
        if not transcript:
            return

        logger.info("[%s] AGENT heard: %s", session.label, transcript)
        patient_text = await asyncio.to_thread(
            session.patient.respond_to_agent, transcript
        )
        logger.info("[%s] PATIENT says: %s", session.label, patient_text)

        await _speak_patient(websocket, session, patient_text)

        if session.patient.should_end_call(patient_text):
            await asyncio.sleep(1.5)
            await _end_call(session)
    finally:
        session.processing = False


def _transcribe_wav(client: OpenAI, wav_bytes: bytes) -> str:
    from io import BytesIO

    file_obj = BytesIO(wav_bytes)
    file_obj.name = "chunk.wav"
    result = client.audio.transcriptions.create(
        model=OPENAI_STT_MODEL,
        file=file_obj,
    )
    return result.text or ""


async def _speak_patient(websocket: WebSocket, session: CallSession, text: str) -> None:
    if not session.stream_sid:
        return

    mp3 = await asyncio.to_thread(_synthesize, session.openai, text)
    chunks = mp3_to_mulaw_chunks(mp3)

    await websocket.send_text(
        json.dumps({"event": "clear", "streamSid": session.stream_sid})
    )

    for chunk in chunks:
        await websocket.send_text(
            json.dumps(
                {
                    "event": "media",
                    "streamSid": session.stream_sid,
                    "media": {"payload": encode_mulaw_payload(chunk)},
                }
            )
        )
        await asyncio.sleep(0.02)


def _synthesize(client: OpenAI, text: str) -> bytes:
    speech = client.audio.speech.create(
        model="tts-1",
        voice=OPENAI_TTS_VOICE,
        input=text,
        response_format="mp3",
    )
    return speech.read()


async def _end_call(session: CallSession) -> None:
    if session.ended or not session.call_sid:
        return
    session.ended = True
    try:
        await asyncio.to_thread(
            lambda: twilio_client().calls(session.call_sid).update(status="completed")
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to end call %s: %s", session.call_sid, exc)


async def _save_transcript(session: CallSession) -> None:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = TRANSCRIPTS_DIR / f"{session.label}.txt"
    json_path = TRANSCRIPTS_DIR / f"{session.label}.json"

    lines = session.transcript_lines()
    header = (
        f"Call label: {session.label}\n"
        f"Scenario: {session.scenario_id}\n"
        f"Call SID: {session.call_sid}\n\n"
    )
    txt_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "label": session.label,
        "scenario_id": session.scenario_id,
        "call_sid": session.call_sid,
        "turns": [
            {"role": t.role, "text": t.text}
            for t in (session.patient.turns if session.patient else [])
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def _post_call_pipeline(call_sid: str, scenario_id: str, label: str) -> None:
    await asyncio.sleep(8)
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    mp3_path = RECORDINGS_DIR / f"{label}.mp3"
    try:
        downloaded = await asyncio.to_thread(
            download_call_recording, call_sid, mp3_path
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Recording download failed for %s: %s", label, exc)
        downloaded = None

    txt_path = TRANSCRIPTS_DIR / f"{label}.txt"
    if not txt_path.exists():
        return

    transcript_text = txt_path.read_text(encoding="utf-8")
    issues = await asyncio.to_thread(
        analyze_transcript_text, transcript_text, label
    )
    append_issues_to_bug_report(label, txt_path, downloaded, issues)
    logger.info("Post-call analysis complete for %s (%s issues)", label, len(issues))
