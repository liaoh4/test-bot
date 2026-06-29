# PivotPoint Orthopedics — Voice Agent Test Bot

Automated caller bot that simulates patients calling the PivotPoint Orthopedics voice agent. Makes outbound calls via Twilio, holds natural conversations using an LLM, records both sides, and generates a structured bug report.

---

## Prerequisites

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) — for MP3 conversion (`brew install ffmpeg`)
- [ngrok](https://ngrok.com/download) — for local tunnel (`brew install ngrok`)
- API keys for: Twilio, Deepgram, ElevenLabs, DeepSeek

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/liaoh4/test-bot.git
cd test-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables**

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_API_KEY` | Twilio API key |
| `TWILIO_API_SECRET` | Twilio API secret |
| `TWILIO_CALLER_NUMBER` | Twilio number to call from |
| `TARGET_PHONE_NUMBER` | PivotPoint agent's phone number |
| `DEEPGRAM_API_KEY` | Deepgram API key |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID for the bot |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `PATIENT_NAME` | Patient name used in scenarios |
| `PATIENT_DOB` | Patient date of birth (YYYY-MM-DD) |
| `USE_NGROK` | Set to `true` to auto-start ngrok tunnel |
| `APP_PORT` | Local server port (default: `8001`) |

---

## Run

**Run all scenarios:**

```bash
python main.py
```

**Run a single scenario:**

```bash
python main.py --scenario happy_path_booking
```

**Available scenario IDs:**

| ID | Description |
|----|-------------|
| `setup_cancel_all` | [Setup] Cancel all existing appointments |
| `unclear_request` | Vague request from non-native English speaker |
| `weekend_appointment` | Patient requests a weekend slot |
| `rescheduling` | Reschedule an existing appointment |
| `faq_questions` | Ask about hours, location, insurance |
| `barge_in_test` | Impatient patient interrupts agent |
| `booking_for_someone_else` | Book on behalf of a family member |
| `intent_recovery` | Patient corrects their initial request |
| `medication_refill` | Request a prescription refill |
| `multilingual` | Patient switches between English and Spanish |
| `role_consistency` | Patient tries to derail the agent off-topic |

> **Tip:** Run `setup_cancel_all` first to clear any existing appointments before running `rescheduling` or other state-dependent scenarios.

---

## Output

After each run, results are saved to:

- `recordings/{scenario_id}_combined.mp3` — mixed audio of both sides
- `transcripts/{scenario_id}.json` — timestamped transcript
- `bug_report_{scenario_id}.md` or `bug_report.md` — structured report with outcome scores and latency metrics
