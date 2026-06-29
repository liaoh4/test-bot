# Architecture

## How It Works

The bot places an outbound call via Twilio, which opens a bidirectional WebSocket media stream to a local FastAPI server. Three async tasks run concurrently: forwarding agent audio to Deepgram for speech-to-text, listening for transcription events, and sending keepalive pings. On `UtteranceEnd`, the agent transcript is sent to DeepSeek to generate a patient reply, which is streamed through ElevenLabs TTS and sent back to Twilio as audio — completing the voice loop.

## Key Design Choices

**Preamble handling.** Voice agents typically play an opening greeting before the patient can speak. Each scenario has a `preamble_duration_sec` window (default 15s). Any agent utterance whose start timestamp falls within this window is tagged `role="preamble"` in the transcript and ignored — it is not added to the conversation history and does not trigger a bot response. This prevents the bot from interrupting the agent's intro.

**Barge-in.** For scenarios with `interruption_turns` set, the bot fires a response on the first `is_final` Deepgram result of the target turn without waiting for `UtteranceEnd`. The time from barge-in trigger to the agent's last word end (`last_word_end` from Deepgram) is recorded as the barge-in yield time — how long the agent kept talking after being interrupted. Multiple barge-ins within a scenario are averaged and reported separately.

**Response time.** Agent response time is measured as the gap between `t_bot_finished` (when the bot's TTS audio ends, derived from first audio sent + audio duration) and `t_next_agent_started` (when the agent's first real word begins in the next turn). The agent start time is taken from `words[0]["start"]` in the first `is_final` Deepgram result, converted to a monotonic clock value via `session.start_time + utterance_start_sec`. Negative values (e.g. agent started speaking before bot finished) are excluded from averages.

**Noise handling.** The agent's audio channel carries continuous background noise that causes Deepgram's `SpeechStarted` event to fire before any real speech begins. To avoid recording noise onset as the utterance start time, `utterance_start_sec` is set from `words[0]["start"]` in the first `is_final` result rather than from `SpeechStarted`. This gives word-level timestamp precision and ensures `ts` in the transcript aligns with what is audible in the recording.
