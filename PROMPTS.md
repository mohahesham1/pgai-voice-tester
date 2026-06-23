# Agentic Development — Prompts Used (Cursor)

Representative prompts used to build and debug this project:

1. **Initial scaffold**
   > Build a Python voice bot for the Pretty Good AI challenge that calls +1-805-439-8008, simulates patient scenarios with an LLM, records/transcribes calls, and writes bug reports. Use Twilio Media Streams + FastAPI.

2. **MCP/voice loop**
   > Implement bidirectional Twilio media stream handling: buffer inbound mu-law audio, detect end-of-turn silence, transcribe with Whisper, generate patient reply with GPT, and stream TTS back as mu-law chunks.

3. **Scenario design**
   > Create 12 diverse patient scenarios including scheduling, refills, insurance questions, Sunday edge case, topic switching, and vague requests.

4. **Post-call QA**
   > After each call, analyze transcript JSON and append structured bug entries to bug_report.md with severity and expected behavior.

5. **Debugging**
   > Fix Twilio webhook not receiving audio — verify wss URL conversion, stream parameters, and FFmpeg pydub conversion for TTS playback.

Use these in your Loom debugging video to show iterative AI-assisted development.
