# Architecture

## How It Works

The bot places an outbound call via Twilio, which opens a bidirectional WebSocket media stream to a local FastAPI server. Three async tasks run concurrently: forwarding agent audio to Deepgram for speech-to-text, listening for transcription events, and sending keepalive pings. On utterance end, the agent transcript is sent to DeepSeek to generate a patient reply, which is streamed through ElevenLabs TTS and sent back to Twilio as audio — completing the voice loop.

## Component Integration

**Twilio.** The bot uses Twilio's outbound call API to initiate calls, with a TwiML webhook that instructs Twilio to open a real-time audio stream over WebSocket. All audio — both incoming from the agent and outgoing from the bot — flows through this single WebSocket connection as raw μ-law encoded audio at 8 kHz. This is the same protocol Twilio uses for inbound calls, so no special configuration is needed on the agent side.

**Speech-to-text (Deepgram).** Incoming agent audio is forwarded in real time to Deepgram's streaming API. Deepgram is configured with utterance-end detection (a silence timeout after which it signals that the speaker has finished) and interim results (partial transcripts that arrive before the speaker stops). Utterance-end is used to trigger the bot's response in normal turns; interim results are used to detect barge-in moments early, before the agent finishes speaking.

**Text-to-speech (ElevenLabs).** The bot uses ElevenLabs' streaming WebSocket API, which begins returning audio chunks before the full text has been generated. Text is flushed to ElevenLabs sentence-by-sentence (on punctuation boundaries) so audio starts playing as soon as the first sentence is ready, rather than waiting for the entire LLM response. The audio arrives as 16 kHz PCM, which is downsampled to 8 kHz and re-encoded as μ-law before being sent to Twilio.

## Key Design Choices

**Preamble handling.** Voice agents typically play an opening greeting before the patient can speak. Each scenario has a configurable preamble window (default 15 seconds). Any agent utterance whose start timestamp falls within this window is tagged as preamble in the transcript and ignored — it is not added to the conversation history and does not trigger a bot response. This prevents the bot from interrupting the agent's intro.

**Barge-in.** For scenarios that test interruption behavior, the bot fires a response mid-turn without waiting for the agent to finish speaking. The time from when the bot first speaks to when the agent stops talking is recorded as the barge-in yield time — measuring how long the agent kept talking after being interrupted. Multiple barge-ins within a scenario are averaged and reported separately.

**Response time.** Agent response time is measured as the gap between when the bot finishes speaking and when the agent's first real word begins in the next turn. The agent's start time is pinned to the first word Deepgram recognizes, so the measurement reflects actual speech rather than silence or processing delay. Negative values — which occur when the agent starts speaking before the bot finishes — are excluded from averages.

**Noise handling.** The agent's audio channel carries continuous background noise that causes Deepgram's speech detection to fire before any real speech begins. To avoid recording noise onset as the utterance start time, the start timestamp is taken from the first recognized word rather than from the initial speech detection event. This gives word-level precision and ensures transcript timestamps align with what is audible in the recording.
