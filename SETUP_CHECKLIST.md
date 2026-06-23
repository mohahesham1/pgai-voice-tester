# Setup Checklist (5 minutes)

## Already done on your machine
- [x] Python dependencies installed
- [x] FFmpeg installed
- [x] `.env` file created from template
- [x] GitHub repo published: https://github.com/mohahesham1/pgai-voice-tester

## You must fill in `.env` (I cannot do this for you — your private accounts)

Open `C:\Users\moham\pgai-voice-tester\.env` and set:

| Variable | Where to get it |
|----------|-----------------|
| `TWILIO_ACCOUNT_SID` | [Twilio Console](https://console.twilio.com/) |
| `TWILIO_AUTH_TOKEN` | Twilio Console |
| `TWILIO_PHONE_NUMBER` | Your Twilio number (E.164, e.g. `+15125551234`) |
| `OPENAI_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys) |
| `PUBLIC_WEBHOOK_URL` | From ngrok after step 2 below |

## Run (3 terminals)

**Terminal 1 — server**
```powershell
cd C:\Users\moham\pgai-voice-tester
.\scripts\start_server.ps1
```

**Terminal 2 — ngrok**
```powershell
ngrok http 8080
```
Copy the `https://....ngrok-free.app` URL into `.env` as `PUBLIC_WEBHOOK_URL`, then restart Terminal 1.

**Terminal 3 — place call**
```powershell
cd C:\Users\moham\pgai-voice-tester
.\scripts\run_one_call.ps1 -Scenario schedule_simple
```

**Full campaign (12 calls)**
```powershell
python scripts\run_campaign.py
```

## Submission reminder
You need **10+ real calls** with files in `recordings/` and `transcripts/`.
