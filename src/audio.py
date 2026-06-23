"""Audio helpers for Twilio 8kHz mu-law media streams."""

from __future__ import annotations

import audioop
import base64
import io
import struct
import wave

from pydub import AudioSegment


def mulaw_to_wav_bytes(mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
    """Convert G.711 mu-law mono bytes to WAV bytes for Whisper."""
    pcm16 = audioop.ulaw2lin(mulaw_data, 2)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16)
    return buffer.getvalue()


def mp3_to_mulaw_chunks(mp3_bytes: bytes, chunk_size: int = 160) -> list[bytes]:
    """
    Convert MP3 TTS output to 8kHz mu-law chunks.
    Twilio expects 160-byte chunks (~20ms at 8kHz mu-law).
    """
    audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
    audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
    pcm = audio.raw_data
    mulaw = audioop.lin2ulaw(pcm, 2)
    return [mulaw[i : i + chunk_size] for i in range(0, len(mulaw), chunk_size)]


def encode_mulaw_payload(chunk: bytes) -> str:
    return base64.b64encode(chunk).decode("ascii")


def decode_mulaw_payload(payload_b64: str) -> bytes:
    return base64.b64decode(payload_b64)


def pcm16_rms(pcm16: bytes) -> float:
    if not pcm16:
        return 0.0
    return audioop.rms(pcm16, 2)


def mulaw_energy(mulaw_chunk: bytes) -> float:
    if not mulaw_chunk:
        return 0.0
    pcm = audioop.ulaw2lin(mulaw_chunk, 2)
    return pcm16_rms(pcm)
