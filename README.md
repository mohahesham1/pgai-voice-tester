# PGAI Voice Patient Simulator

Automated **voice bot** for the [Pretty Good AI Engineering Challenge](https://pgai.us/athena).  
It calls the assessment line **`+1-805-439-8008`**, simulates realistic patient conversations, records audio, saves transcripts, and documents agent quality issues.

> **Assessment rule:** Only call `+1-805-439-8008`. Do not call numbers shown on the Athena signup confirmation screen.

---

## What This Repo Delivers

| Deliverable | Location |
|-------------|----------|
| Python voice bot | `src/` |
| Setup + run instructions | this README |
| Architecture (1–2 paragraphs) | `ARCHITECTURE.md` |
| Call recordings (mp3) | `recordings/` (generated after calls) |
| Transcripts (both sides) | `transcripts/` |
| Bug report | `bug_report.md` |
| Scenario library (12 cases) | `src/scenarios.py` |

**Submission minimum:** 10+ full calls (typically 1–3 minutes each) with mp3/ogg + transcripts.

---

## How It Works

```
run_campaign.py / call_runner.py
        │
        ▼
   Twilio outbound call ──► +1-805-439-8008 (Athena agent)
        │
        ▼
FastAPI webhook server (src/server.py)
  • Media Stream WebSocket
  • STT (Whisper) → Patient LLM → TTS
  • Saves transcript + downloads recording
  • LLM QA → bug_report.md
```

---

## Prerequisites

- Python 3.10+
- [Twilio account](https://www.twilio.com/) with a voice-capable phone number (caller ID)
- [OpenAI API key](https://platform.openai.com/) (LLM + STT + TTS)
- [FFmpeg](https://ffmpeg.org/) installed and on `PATH` (required by `pydub` for TTS conversion)
- [ngrok](https://ngrok.com/) (or similar) to expose local webhook server to Twilio

Typical total cost for 10–12 short test calls is under ~$20 (Twilio + OpenAI usage).

---

## Setup

```powershell
cd C:\Users\moham\pgai-voice-tester
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
PUBLIC_WEBHOOK_URL=https://YOUR-NGROK-SUBDOMAIN.ngrok-free.app
OPENAI_API_KEY=...
```

`TARGET_PHONE_NUMBER` is locked to `+1805434398008` in code validation — wait, I used +18054398008 in config. Let me verify - challenge says +1-805-439-8008 which is +18054398008. Good.

---

## Run (3 terminals)

### Terminal 1 — Webhook + media stream server

```powershell
cd C:\Users\moham\pgai-voice-tester
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.server:app --host 0.0.0.0 --port 8080
```

### Terminal 2 — Public tunnel

```powershell
ngrok http 8080
```

Copy the `https://....ngrok-free.app` URL into `.env` as `PUBLIC_WEBHOOK_URL`, then restart Terminal 1 if it was already running.

### Terminal 3 — Place calls

**Single test call:**

```powershell
python -m src.call_runner --scenario schedule_simple
```

**Full campaign (12 scenarios, meets 10-call minimum):**

```powershell
python scripts/run_campaign.py
```

Outputs:

- `recordings/call-01-schedule_simple.mp3`
- `transcripts/call-01-schedule_simple.txt`
- auto-appended findings in `bug_report.md`

---

## Scenarios

| ID | Purpose |
|----|---------|
| `schedule_simple` | Routine appointment booking |
| `reschedule` | Move existing appointment |
| `cancel` | Cancel appointment |
| `medication_refill` | Prescription refill |
| `office_hours` | Hours / weekend question |
| `location_insurance` | Address + insurance |
| `vague_request` | Unclear medical need |
| `topic_change` | Switch intent mid-call |
| `sunday_edge` | Weekend scheduling edge case |
| `interruption` | Fast/multi-question flow |
| `wrong_info_correction` | DOB correction |
| `multi_request` | Refill + labs + scheduling |

List all:

```powershell
python -c "from src.scenarios import list_scenario_ids; print('\n'.join(list_scenario_ids()))"
```

---

## Submission Checklist

- [ ] 10+ real calls completed against `+1-805-439-8008`
- [ ] MP3 (or OGG) files in `recordings/`
- [ ] Transcripts in `transcripts/`
- [ ] `bug_report.md` populated with useful issues
- [ ] Public GitHub repo link
- [ ] Loom walkthrough (≤5 min)
- [ ] Loom AI-debugging session (≤5 min)
- [ ] Submit form with **one** E.164 caller ID (your Twilio number)

---

## Security

- Never commit `.env` or API keys
- `.gitignore` excludes generated recordings/transcripts by default
- Rotate keys if accidentally exposed

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Twilio can't reach webhook | Confirm ngrok URL in `.env` matches active tunnel |
| No audio / bot silent | Install FFmpeg; check OpenAI TTS quota |
| Empty transcript | Verify Media Stream WebSocket connected (server logs) |
| `TARGET_PHONE_NUMBER` error | Must remain `+18054398008` |
| Call drops quickly | Check Twilio balance and number voice permissions |

---

## Project Structure

```
pgai-voice-tester/
├── src/
│   ├── server.py          # Twilio webhooks + voice loop
│   ├── call_runner.py     # Single call CLI
│   ├── scenarios.py       # Patient scenarios
│   ├── patient_agent.py   # LLM patient persona
│   ├── analyzer.py        # Post-call bug extraction
│   ├── twilio_client.py   # Outbound call + recording download
│   └── audio.py           # mu-law / TTS conversion
├── scripts/run_campaign.py
├── recordings/
├── transcripts/
├── bug_report.md
├── ARCHITECTURE.md
└── requirements.txt
```

---

## License

MIT — built for the Pretty Good AI engineering assessment.
