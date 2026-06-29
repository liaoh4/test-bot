# Booking Caller Bot — Project Context

## What This Is

A standalone Python tool that acts as an automated "patient" caller to test the
Vocaline appointment booking voice agent. It makes outbound phone calls, has
natural conversations using an LLM, records both sides, transcribes them, and
reports any bugs or quality issues found in the agent's responses.

This is a testing tool only — it is not part of the Vocaline product itself.

---

## The System Being Tested (Vocaline)

**Product**: Vocaline — a multi-tenant AI voice agent for appointment booking.
Clinics sign up and get a Twilio phone number. When patients call that number,
an AI agent answers, handles scheduling, rescheduling, cancellations, and
general questions via voice.

**Backend repo**: `appointment-agent-backend` (Python / FastAPI)
**Frontend repo**: `appointment-agent-frontend` (Next.js)
**Deployed at**: `api.infiniteaivision.com` (backend), `admin.infiniteaivision.com` (frontend)

**Voice stack**:
- Twilio: telephony (inbound calls, WebSocket media streams)
- Deepgram: speech-to-text (streaming)
- ElevenLabs: text-to-speech
- DeepSeek: LLM for agent reasoning and tool calls

**Agent behavior**: When a call comes in, the backend opens a WebSocket with
Twilio, streams audio to Deepgram for transcription, feeds transcripts to
DeepSeek with a system prompt, and streams ElevenLabs TTS audio back to the
caller. The agent can book, reschedule, cancel appointments, and answer
clinic-specific questions using tool calls against the PostgreSQL database.

**To test the agent**: Call the org's Twilio phone number. You can find it in
the `org_settings` table (`org_phone` column) in the Railway PostgreSQL database.

---

## What This Project Should Build

An automated caller bot that:

1. **Makes outbound calls** via Twilio to the Vocaline agent's phone number
2. **Simulates a patient** — uses an LLM (DeepSeek or similar) to generate
   realistic responses in real time based on a predefined scenario
3. **Speaks via TTS** — converts LLM responses to audio and plays them into the call
4. **Listens via STT** — transcribes what the Vocaline agent says
5. **Records the call** — saves audio (mp3/ogg) and transcript for each call
6. **Runs multiple scenarios** — scheduling, rescheduling, cancellation, edge cases
7. **Generates a bug report** — after all calls, summarizes issues found

---

## Suggested Architecture

```
main.py
  └── runs N test scenarios sequentially

caller_bot.py
  └── for each scenario:
      - initiate outbound Twilio call
      - open WebSocket or use Twilio media streams
      - STT: stream agent audio → Deepgram → text
      - LLM: feed transcript + scenario → DeepSeek → next patient utterance
      - TTS: ElevenLabs → audio → play into call
      - record both sides
      - detect end of conversation (agent hangs up or silence timeout)

scenarios.py
  └── list of test scenarios, each with:
      - patient persona (name, reason for calling)
      - goal (what the patient wants to achieve)
      - edge case notes (e.g. "ask for Sunday appointment")

reporter.py
  └── reads all transcripts, uses LLM to identify bugs/issues
      outputs bug_report.md
```

---

## Tech Stack (reuse existing accounts)

| Component | Tool | Notes |
|-----------|------|-------|
| Outbound call | Twilio | Same account as Vocaline backend |
| STT | Deepgram | Same API key |
| TTS | ElevenLabs | Same API key |
| LLM | DeepSeek | Same API key |
| Recording | Twilio built-in or local audio capture | |
| Language | Python 3.11+ | |

---

## Test Scenarios to Cover

1. Simple appointment scheduling (happy path)
2. Scheduling with no available slots
3. Rescheduling an existing appointment
4. Cancellation
5. Asking for a weekend appointment (clinic closed)
6. Unclear / mumbled request
7. Patient interrupts the agent mid-sentence
8. Patient asks about insurance / location / hours
9. Patient gives wrong information and then corrects it
10. Patient tries to book for someone else

---

## Key Design Decisions to Make

- **How to play audio into the call**: Twilio outbound calls can use `<Stream>` TwiML
  to open a media stream WebSocket, same as the inbound flow in the Vocaline backend.
  The caller bot connects to this WebSocket and sends/receives μ-law audio.
- **Turn-taking**: Listen until 1-2 seconds of silence after the agent speaks,
  then generate a response. Don't interrupt unless testing barge-in.
- **Recording**: Record the raw audio stream on both sides locally, then convert
  to mp3 for submission.

---

## Environment Variables Needed

```
TWILIO_ACCOUNT_SID=
TWILIO_API_KEY=
TWILIO_API_SECRET=
TWILIO_CALLER_NUMBER=   # the Twilio number to call FROM (must be verified)
TARGET_PHONE_NUMBER=    # the Vocaline org's phone number to call
DEEPGRAM_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
DEEPSEEK_API_KEY=
WEBHOOK_BASE_URL=       # ngrok or similar, for Twilio to reach this bot's webhook
```

---

## Deliverables

- `main.py` — entry point, runs all scenarios
- `caller_bot.py` — core call logic
- `scenarios.py` — test scenario definitions
- `reporter.py` — bug report generator
- `recordings/` — audio files (mp3/ogg)
- `transcripts/` — text transcripts per call
- `bug_report.md` — final bug report
- `README.md` — setup and run instructions
- `.env.example` — required environment variables

---

## Notes

- The caller bot needs a public webhook URL (ngrok locally, or deploy to Railway)
  so Twilio can POST the call status and open the media stream.
- The `TWILIO_CALLER_NUMBER` must be a different Twilio number than the one
  Vocaline is listening on (you can't call yourself from the same number).
- Start simple: get one full conversation working before adding scenarios.
