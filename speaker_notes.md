# Speaker Notes — Project Walkthrough (under 5 min)

## 1. Intro (0:00–0:25)

This project is a voice agent test bot for PivotPoint Orthopedics — an automated caller that simulates real patients, holds natural conversations with an LLM, records both sides, and turns each call into a structured bug report with quantitative metrics, not just a transcript.

## 2. Project structure (0:25–1:00)

The codebase is six files, each with one job: `main.py` is the entry point — it starts the local server, runs the selected scenarios through `run_scenarios()`, and kicks off the report at the end. `caller_bot.py` is the core call engine — `CallerBot.run_scenario()` places the outbound Twilio call, and the WebSocket handler runs the live voice loop I'm about to walk through. `scenarios.py` defines each test case as a `Scenario` — persona, goal, preamble window, interruption turns. `audio_utils.py` handles audio encoding and mixes the final combined recording. `reporter.py` scores a finished call and writes the markdown bug report. And `config.py` just loads all the API keys and settings from `.env`.

## 3. The voice loop (1:00–1:45)

The bot places an outbound call through Twilio, which opens a bidirectional WebSocket audio stream to a local FastAPI server — the same protocol Twilio uses for real inbound calls, so nothing special is needed on the agent's side. Two async tasks run concurrently: forwarding agent audio to Deepgram, and listening for transcription events. On utterance-end, the transcript goes to DeepSeek, which generates a reply. That reply is flushed to ElevenLabs sentence by sentence, so audio starts streaming back as soon as the first sentence is ready rather than waiting on the full response. That audio is sent back to Twilio, completing the loop.

## 4. Challenges we ran into (1:45–3:30)

That's the loop when everything goes smoothly — getting there took a few wrong turns along the way, and each one shaped a specific design decision:

- **The agent's own greeting kept getting interrupted.** Voice agents open with a scripted intro, and early on the bot would jump in mid-greeting. The fix was a configurable preamble window — anything the agent says in that window is tagged and excluded from the conversation entirely. The window length can be set per scenario, so it can be tuned to whatever a given test requires.
- **Background noise was tripping speech detection.** The agent's line has constant background noise, and Deepgram's detector kept firing before real speech started, throwing off every downstream timestamp. The fix was to anchor the utterance start to the first *recognized word* rather than the initial detection event.
- **Keeping it all on one clock.** All of this depends on one shared clock, captured the moment the call connects — every Deepgram and TTS timestamp gets projected onto it. That's also what lets me rebuild the audio afterward: each turn's wall-clock timestamp converts directly into a byte offset in the combined recording, so the final MP3 and the JSON transcript line up, timestamp for timestamp.

## 5. How we score each call (3:30–4:15)

That timing data feeds directly into scoring. Evaluation follows a priority order, not a flat checklist: first, did the agent complete the task and get the outcome right — judged by DeepSeek reading the full transcript. Only if that passes do we look at quality — did it re-ask for information already given, how quickly did it respond, how well did it yield during barge-in. A call that fails on task completion counts as a bug regardless of how good those quality numbers look.
