# Booking Caller Bot — Test Tool for Vocaline

## Context
Vocaline is a live AI voice booking agent. This project builds a standalone **automated caller bot** that acts as a fake patient, makes outbound calls to Vocaline's Twilio number, holds realistic conversations, records both sides, and generates a structured bug report. Testing tool only — not part of Vocaline.

---

## File Structure

```
test_agent/
├── main.py              # Entry point — CLI args, runs scenarios, calls reporter
├── caller_bot.py        # Core call logic: Twilio outbound + WS handler
├── scenarios.py         # Scenario definitions (10 test cases)
├── reporter.py          # Structured scoring + markdown report generator
├── config.py            # pydantic-settings env var singleton
├── audio_utils.py       # mulaw ↔ base64, file write, mp3 conversion
├── recordings/          # Created at runtime — mp3 per call
├── transcripts/         # Created at runtime — JSON transcript per call
├── bug_report.md        # Generated after scenarios finish
├── requirements.txt
├── .env
└── .env.example
```

---

## Architecture

```
main.py (CLI: --scenario <id> or all)
  └── start FastAPI + ngrok once
  └── for each selected Scenario:
        result = await bot.run_scenario(scenario)   → CallResult
  └── reporter.generate_report(results) → bug_report.md

caller_bot.run_scenario()
  1. POST Twilio REST → create outbound call, url={WEBHOOK_BASE_URL}/twiml
  2. Twilio fetches /twiml → <Connect><Stream url="wss://.../ws/{call_sid}">
  3. Twilio opens WebSocket → asyncio.gather(
       receive_from_twilio(twilio_ws, dg_ws, session),
       receive_from_deepgram(dg_ws, session),
     )
  4. On speech_final (or barge-in trigger for interruption scenarios):
       bot_respond(session)
  5. On end: save transcript JSON + recording mp3, return CallResult
```

---

## `config.py`
`pydantic-settings` `Settings` singleton:
```
TWILIO_ACCOUNT_SID, TWILIO_API_KEY, TWILIO_API_SECRET
TWILIO_CALLER_NUMBER   # bot's "from" number
TARGET_PHONE_NUMBER    # Vocaline org number
DEEPGRAM_API_KEY
ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
DEEPSEEK_API_KEY
WEBHOOK_BASE_URL       # updated at startup if USE_NGROK=true
USE_NGROK=true
APP_PORT=8001
```

---

## `scenarios.py`
```python
@dataclass
class Scenario:
    id: str
    name: str
    patient_name: str
    patient_dob: str
    persona_prompt: str        # patient LLM system prompt
    edge_case_notes: str       # passed to reporter for human context
    interruption_turn: int | None = None  # if set, bot speaks at this turn even if agent still talking
    max_duration_sec: int = 120
```

10 scenarios (from CONTEXT.md). `interruption_turn` is non-None only for scenario 7 (barge-in test). All others default to `None` (no interruption).

---

## `audio_utils.py`
- `b64_encode(data: bytes) -> str`
- `b64_decode(data: str) -> bytes`
- `make_media_event(stream_sid, b64) -> dict`
- `make_clear_event(stream_sid) -> dict`
- `save_recording(call_id: str, mulaw_bytes: bytes) -> Path` — writes to `recordings/`, converts to mp3 via `ffmpeg`

---

## `caller_bot.py`

### `CallSession` dataclass
```python
@dataclass
class CallSession:
    call_sid: str
    stream_sid: str
    scenario: Scenario
    twilio_ws: WebSocket
    conversation_history: list[dict]   # seeded with persona_prompt as system
    transcript: list[dict]             # {"role": "agent"|"bot", "text": str, "ts": float}
    agent_audio_buf: bytearray
    bot_audio_buf: bytearray
    turn_timestamps: list[dict]        # {"t_agent_finished": float, "t_first_audio_sent": float}
    start_time: float
    current_turn: int = 0
    is_agent_speaking: bool = False    # tracks whether agent audio is actively arriving
    barge_in_start_ts: float | None = None  # set when bot speaks into agent turn
    observed_response_ms: float | None = None  # external observation for interruption scenarios
```

### `receive_from_twilio(twilio_ws, dg_ws, session)`
- `"start"` → set `stream_sid`
- `"media"` → decode bytes → append to `agent_audio_buf` → `await dg_ws.send(bytes)` → set `session.is_agent_speaking = True`, update `session.last_audio_at`
- `"stop"` → close dg_ws, break
- Silence detection (side task): if `time() - last_audio_at > 1.5s` → set `is_agent_speaking = False`; threshold aligns with Deepgram `utterance_end_ms=1000` to avoid treating natural pauses as end-of-speech. If this was during an active barge-in, compute `observed_response_ms = now - barge_in_start_ts`

### `receive_from_deepgram(dg_ws, session)`
- Accumulate agent transcript
- On `speech_final=True`:
  - Record `t_agent_finished = time.monotonic()`
  - `session.current_turn += 1`
  - Check interruption: if `scenario.interruption_turn == session.current_turn` → fire `bot_respond` immediately (even if `is_agent_speaking`)
  - Otherwise: fire `bot_respond` only if not `is_agent_speaking` (default: no interruption)
- `create_task(bot_respond(session, t_agent_finished))`

### `bot_respond(session, t_agent_finished)`
**Interruption logic**:
- Default: bot waits for `speech_final` (agent finished). `is_agent_speaking` flag is informational but bot never cancels/clears agent audio — that's Vocaline's internal concern.
- Interruption scenario only: if `scenario.interruption_turn` matches current turn, bot speaks while agent is still sending audio. Set `session.barge_in_start_ts = time.monotonic()`. When `is_agent_speaking` subsequently flips to `False` (silence detection), compute and store `observed_response_ms`.
  - Note: `observed_response_ms` measures the gap from bot first speaking to agent audio stopping — it's an external behavioral observation, not Vocaline's internal processing latency.

**End-of-conversation detection** (robust approach):
```python
def conversation_is_over(session: CallSession) -> bool:
    recent = [t["text"].lower() for t in session.transcript[-4:] if t["role"] == "agent"]
    closing_phrases = [
        "goodbye", "bye", "have a good", "take care", "thank you for calling",
        "is there anything else", "anything else i can", "all set", "all done",
        "your appointment has been", "we'll see you", "see you then",
    ]
    keyword_hit = any(phrase in turn for turn in recent for phrase in closing_phrases)
    if not keyword_hit:
        return False  # no keyword → skip LLM entirely, keep going
    # Keyword matched → semantic confirmation via LLM
    # Called AFTER bot TTS is fully sent so it doesn't affect latency measurement
    return _llm_goal_check(session)  # returns bool
# KNOWN LIMITATION: keyword list may miss novel Vocaline phrasings; if so the call
# runs to max_duration_sec and force-hangs. Improve in v2 with Vocaline-specific tuning.
```

**Main flow**:
1. Check `conversation_is_over` → if yes, bot says a natural goodbye via TTS, hang up
2. Call DeepSeek LLM with `conversation_history` → patient reply text
3. Append bot turn to `transcript` and `conversation_history`
4. Stream ElevenLabs (ulaw_8000) → on **first chunk**: record `t_first_audio_sent = time.monotonic()`; append `{"t_agent_finished": t_agent_finished, "t_first_audio_sent": t_first_audio_sent}` to `session.turn_timestamps`
5. Send all mulaw chunks as Twilio `media` events; append to `bot_audio_buf`

### End-of-call cleanup
In `finally` block of WS handler:
- `twilio.calls(call_sid).update(status="completed")`
- Save `transcripts/{scenario.id}.json`
- `audio_utils.save_recording(scenario.id, session.agent_audio_buf)` (agent side)

---

## `reporter.py`

### Data structures
```python
@dataclass
class TurnTimestamp:
    t_agent_finished: float
    t_first_audio_sent: float

    @property
    def latency_ms(self) -> float:
        return (self.t_first_audio_sent - self.t_agent_finished) * 1000

@dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    edge_case_notes: str
    transcript: list[dict]
    turn_timestamps: list[TurnTimestamp]
    observed_response_ms: float | None    # interruption scenarios only

    # --- Task layer (LLM-extracted, verbatim from transcript) ---
    patient_final_intent: str | None      # verbatim excerpt from transcript
    agent_final_action: str | None        # verbatim excerpt; None if task incomplete
    task_completed: bool                  # = (agent_final_action is not None)
    outcome_correct: bool | None          # None if task_completed=False
    mismatch_excerpt: str | None          # free-text for human localization

    # --- Quality layer (deterministic code) ---
    redundant_repeats: int                # slots asked twice when patient already answered

    # --- Efficiency layer ---
    turns_to_completion: int
    avg_response_latency_ms: float
    max_response_latency_ms: float
```

### Task layer — LLM extraction
Single LLM call per scenario. Prompt instructs the model to:
- Quote `patient_final_intent` verbatim from the last patient utterance expressing their goal
- Quote `agent_final_action` verbatim from the last agent utterance confirming an action taken (or `null` if none)
- Set `outcome_correct = true` only if both excerpts clearly point to the same outcome
- Set `mismatch_excerpt` to the verbatim agent line where the mismatch is most visible (or `null`)
- **No inference, no rephrasing, no failure categorization** — extract only what is literally said

LLM returns structured JSON. Parsed into `ScenarioResult` fields. No free-text summarization at this layer.

### Quality layer — deterministic code
`count_redundant_repeats(transcript: list[dict]) -> int`:
- Parse agent turns for question patterns (e.g. "what is your name", "date of birth", "what day", "what time")
- For each slot, check if a prior patient turn already contains a plausible answer (non-empty, non-filler response)
- If agent asks same slot again after patient answered → increment counter
- If agent re-asks because patient said "I don't know" / gave no answer → do NOT increment
- Implementation: regex-based slot detection, no LLM

### Efficiency layer — computed from `turn_timestamps`
```python
latencies = [ts.latency_ms for ts in result.turn_timestamps]
avg_response_latency_ms = mean(latencies)
max_response_latency_ms = max(latencies)
turns_to_completion = len(result.turn_timestamps)
```

### Report rendering
After all `ScenarioResult` objects are built, render `bug_report.md`:
- Summary table: one row per scenario (task_completed, outcome_correct, redundant_repeats, avg/max latency, turns)
- Per-scenario section: structured fields first, then transcript excerpt (mismatch_excerpt highlighted)
- No LLM-generated prose summaries — all content comes from the structured fields

---

## `main.py`
```python
# CLI: python main.py [--scenario <id>]
# --scenario omitted → run all 10
# --scenario happy_path_booking → run only that one

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--scenario", type=str, default=None)
args = parser.parse_args()

selected = [s for s in ALL_SCENARIOS if args.scenario is None or s.id == args.scenario]
if not selected:
    print(f"Unknown scenario: {args.scenario}")
    sys.exit(1)
```

---

## Environment Variables (`.env.example`)
```bash
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_API_KEY=SKxxx
TWILIO_API_SECRET=xxx
TWILIO_CALLER_NUMBER=+1555CALLER
TARGET_PHONE_NUMBER=+1555VOCALINE
DEEPGRAM_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
ELEVENLABS_VOICE_ID=xxx
DEEPSEEK_API_KEY=sk-xxx
WEBHOOK_BASE_URL=https://REPLACE.ngrok.io
USE_NGROK=true
APP_PORT=8001
```

## `requirements.txt`
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
websockets>=12.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
twilio>=9.0.0
openai>=1.30.0
httpx>=0.27.0
pyngrok>=7.1.0
```

---

## Build Order
1. `config.py` + `.env`
2. `scenarios.py` — all 10 scenarios, `interruption_turn` set on scenario 7
3. `audio_utils.py`
4. `caller_bot.py` — FastAPI routes + WS handler + `CallerBot`
5. `main.py` — CLI + orchestration loop + ngrok startup
6. `reporter.py` — scoring layers + markdown render

Start with scenario 1 (happy path) end-to-end before wiring up all 10.

---

## Verification
1. `python main.py --scenario happy_path_booking` → ngrok starts, single call placed
2. Confirm `transcripts/happy_path_booking.json` written with agent + bot turns and `turn_timestamps`
3. Confirm `recordings/happy_path_booking.mp3` saved
4. `python main.py --scenario barge_in_test` → confirm `observed_response_ms` populated
5. `python main.py` → all 10 scenarios → `bug_report.md` generated with summary table
6. Manually review one transcript against `ScenarioResult` fields for accuracy
