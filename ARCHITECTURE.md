# Architecture

## How It Works

The bot places an outbound call via Twilio, which opens a bidirectional WebSocket media stream to a local FastAPI server. Two async tasks run concurrently: forwarding agent audio to Deepgram for speech-to-text, and listening for transcription events. On utterance end, the agent transcript is sent to DeepSeek to generate a patient reply, which is streamed through ElevenLabs TTS and sent back to Twilio as audio — completing the voice loop.


## Key Design Choices

1. **Preamble handling.** Voice agents typically play an opening greeting before the patient can speak. Each scenario has a configurable preamble window (tunable per scenario, default 15 seconds). Any agent utterance whose start timestamp falls within this window is tagged as preamble and excluded from the conversation history — it does not trigger a bot response. This prevents the bot from interrupting the agent's intro.

2. **Noise handling.** The agent's audio channel carries continuous background noise that causes Deepgram's speech detector to fire before any real speech begins, which would otherwise throw off every downstream timestamp. To avoid recording noise onset as the utterance start time, the start timestamp is taken from the first recognized word rather than from the initial detection event, giving word-level precision.

3. **Shared timestamp clock.** Both of the above depend on a single shared clock, `session.start_time`, captured at call connect. Every Deepgram and TTS timestamp is projected onto this common timeline, which is also what allows the recorded audio to be reconstructed after the call: each turn's wall-clock timestamp converts directly into a byte offset in the combined recording, keeping the final MP3 and the JSON transcript aligned timestamp for timestamp.