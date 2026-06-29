# Test Bot — New Agent Roadmap

## Overview

This project is forked from `booking-agent-tests`. The core infrastructure
(Twilio WebSocket, Deepgram STT, DeepSeek LLM, ElevenLabs TTS, audio
recording, transcript with timestamps) is reused as-is. Changes are limited
to the business layer and a new preamble feature.

Target: local-only runs, no CI/CD.

---

## Step 1 — Copy & clean up

- Copy the `booking-agent-tests` repo into a new local directory
- Delete runtime artifacts: `recordings/`, `transcripts/`, `reports/`
- Remove `.github/` (no CI/CD needed)
- Update `README` or delete it

---

## Step 2 — Config

Edit `config.py` (or `.env`):

- [ ] Set `TARGET_PHONE_NUMBER` to the new agent's number
- [ ] Confirm all API keys still valid (Twilio, Deepgram, DeepSeek, ElevenLabs)
- [ ] Set `WEBHOOK_BASE_URL` to your local tunnel (e.g. ngrok)

---

## Step 3 — Add preamble support

### `scenarios.py`
Add field to `Scenario` dataclass:
```python
preamble_duration_sec: float = 0
```

### `caller_bot.py`
In `_receive_from_deepgram`, at both the `UtteranceEnd` and barge-in
handling points, add a preamble check using the utterance **start time**
(not the UtteranceEnd fire time):

```python
in_preamble = utterance_start_sec is not None and \
    utterance_start_sec < session.scenario.preamble_duration_sec
```

During preamble:
- Append to `session.transcript` with `role="preamble"` (for analysis)
- Do NOT add to `session.conversation_history`
- Do NOT call `_schedule_response`
- Reset `utterance_start_sec = None` and continue

After preamble: normal flow unchanged.

---

## Step 4 — Write scenarios

Create new scenarios in `scenarios.py` for the new agent:

- [ ] Map out the agent's conversation flow and business goal
- [ ] Write scenarios covering: happy path, edge cases, error paths
- [ ] Set `preamble_duration_sec=15` on each scenario (adjust after first run)
- [ ] Write `edge_case_notes` per scenario — used by `_llm_goal_check` to
      decide if the conversation reached a natural end
- [ ] Set `max_duration_sec` conservatively (preamble eats into the budget)

---

## Step 5 — Adjust bot persona

Edit the `persona_prompt` template in `register_session` (or per-scenario):

- [ ] Match the new agent's domain (replace appointment-booking persona)
- [ ] Decide if the bot needs to handle any Spanish during/after preamble
- [ ] Keep the speaking-style rules (natural dates/times, spoken language)

---

## Step 6 — First run & calibration

- [ ] Start a local tunnel (`ngrok http 8000` or equivalent)
- [ ] Run the server (`uv run python main.py` or equivalent entry point)
- [ ] Trigger a single simple scenario and listen to the recording
- [ ] Verify preamble utterances appear as `role="preamble"` in transcript
- [ ] Verify `ts` / `ts_end` in transcript align with positions in the audio file
- [ ] Adjust `preamble_duration_sec` based on actual preamble length observed
- [ ] Check `observed_response_ms` is being captured on barge-in scenarios

---

## Step 7 — Filler audio (if needed)

If the new agent has a short no-input timeout (agent re-prompts before bot
finishes LLM + TTS), add filler audio:

- After `UtteranceEnd`, before `_schedule_response`, immediately play a
  short filler clip ("Um...", breath sound) via `_speak` to reset the
  agent's VAD timeout
- Then let the full LLM + TTS response play normally

Defer this until Step 6 confirms it is actually needed.

---

## Files that do NOT need changes

| File | Reason |
|------|--------|
| `audio_utils.py` | Audio mixing / WAV writing logic is generic |
| `caller_bot.py` (pipeline) | Twilio WS, Deepgram, LLM streaming, TTS unchanged |
| `config.py` (structure) | Only values change, not structure |
| Transcript / recording save logic | Already generic |
