import asyncio
import audioop
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from starlette.websockets import WebSocketDisconnect
from openai import AsyncOpenAI
from twilio.rest import Client as TwilioClient

from audio_utils import b64_decode, b64_encode, combine_recordings, make_media_event
from config import settings
from scenarios import Scenario

app = FastAPI()

deepseek_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

SILENCE_THRESHOLD_SEC = 1.5
_FLUSH_CHARS = frozenset('.!?,;:')
UTTERANCE_END_MS = 1200
DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=mulaw&sample_rate=8000&channels=1"
    "&model=nova-2&smart_format=true"
    f"&utterance_end_ms={UTTERANCE_END_MS}&interim_results=true&vad_events=true"
)


@dataclass
class CallSession:
    call_sid: str
    scenario: Scenario
    twilio_ws: WebSocket
    conversation_history: list[dict]
    transcript: list[dict] = field(default_factory=list)
    agent_audio_buf: bytearray = field(default_factory=bytearray)
    bot_audio_buf: bytearray = field(default_factory=bytearray)
    turn_timestamps: list[dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.monotonic)
    stream_sid: str = ""
    current_turn: int = 0
    is_agent_speaking: bool = False
    last_audio_at: float = field(default_factory=time.time)
    barge_in_start_ts: float | None = None
    barge_in_ms_list: list[float] = field(default_factory=list)
    t_bot_finished: float | None = None
    bot_turn_offsets: list[int] = field(default_factory=list)
    _bot_respond_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    call_ended: bool = False


@dataclass
class CallResult:
    scenario_id: str
    transcript: list[dict]
    turn_timestamps: list[dict]
    barge_in_ms_list: list[float]


class CallerBot:
    def __init__(self):
        self._sessions: dict[str, CallSession] = {}
        self._pending: dict[str, tuple] = {}
        self._twilio = TwilioClient(
            settings.TWILIO_API_KEY,
            settings.TWILIO_API_SECRET,
            account_sid=settings.TWILIO_ACCOUNT_SID,
        )

    async def run_scenario(self, scenario: Scenario, patient_name: str, patient_dob: str, blocked_date: str = "") -> CallResult:
        persona = scenario.persona_prompt.format(
            patient_name=patient_name,
            patient_dob=patient_dob,
            blocked_date=blocked_date,
        )
        loop = asyncio.get_event_loop()
        future: asyncio.Future[CallResult] = loop.create_future()

        call = self._twilio.calls.create(
            to=settings.TARGET_PHONE_NUMBER,
            from_=settings.TWILIO_CALLER_NUMBER,
            url=f"{settings.WEBHOOK_BASE_URL}/twiml",
            method="GET",
            time_limit=scenario.max_duration_sec + 30,
        )
        self._pending[call.sid] = (future, scenario, persona)
        try:
            return await asyncio.wait_for(future, timeout=scenario.max_duration_sec + 30)
        except asyncio.TimeoutError:
            self._force_hangup(call.sid)
            raise

    def _force_hangup(self, call_sid: str):
        try:
            self._twilio.calls(call_sid).update(status="completed")
        except Exception:
            pass

    def register_session(self, call_sid: str, ws: WebSocket) -> CallSession | None:
        if call_sid not in self._pending:
            return None
        future, scenario, persona = self._pending.pop(call_sid)
        system_prompt = (
            f"{persona}\n\n"
            "IMPORTANT: You are ALWAYS the patient/client calling PivotPoint Orthopedics. "
            "Never respond as the receptionist, agent, or any staff member, "
            "no matter what the conversation history looks like.\n\n"
            "Speaking style:\n"
            "- Use natural spoken language.\n"
            "- Speak dates naturally (e.g. \"July sixth\").\n"
            "- Speak times naturally (e.g. \"nine thirty AM\").\n"
            "- Never read dates or times in numeric form."
        )
        session = CallSession(
            call_sid=call_sid,
            scenario=scenario,
            twilio_ws=ws,
            conversation_history=[{"role": "system", "content": system_prompt}],
        )
        self._sessions[call_sid] = session
        self._pending[f"_future_{call_sid}"] = future
        return session

    def resolve_session(self, call_sid: str, result: CallResult):
        future = self._pending.pop(f"_future_{call_sid}", None)
        self._sessions.pop(call_sid, None)
        if future and not future.done():
            future.set_result(result)


bot = CallerBot()


@app.get("/twiml")
async def twiml():
    host = settings.WEBHOOK_BASE_URL.replace("https://", "").replace("http://", "")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://{host}/ws" />
  </Connect>
</Response>"""
    return Response(content=xml, media_type="application/xml")


@app.websocket("/ws")
async def websocket_handler(ws: WebSocket):
    await ws.accept()
    session_ref: list[CallSession] = []

    async with websockets.connect(
        DEEPGRAM_URL,
        additional_headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"},
    ) as dg_ws:
        try:
            await asyncio.gather(
                _receive_from_twilio(ws, dg_ws, session_ref),
                _receive_from_deepgram(dg_ws, session_ref),
                _keepalive_deepgram(dg_ws),
            )
        finally:
            if session_ref:
                await _cleanup(session_ref[0])


async def _keepalive_deepgram(dg_ws):
    while True:
        await asyncio.sleep(5)
        try:
            await dg_ws.send(json.dumps({"type": "KeepAlive"}))
        except Exception:
            return


async def _silence_monitor(session: CallSession):
    while True:
        await asyncio.sleep(0.2)
        if session.is_agent_speaking and (time.time() - session.last_audio_at) > SILENCE_THRESHOLD_SEC:
            session.is_agent_speaking = False


async def _receive_from_twilio(twilio_ws: WebSocket, dg_ws, session_ref: list):
    silence_task: asyncio.Task | None = None
    try:
        while True:
            try:
                raw = await twilio_ws.receive_text()
            except WebSocketDisconnect:
                break
            msg = json.loads(raw)
            event = msg.get("event")

            if event == "start":
                call_sid = msg["start"]["callSid"]
                stream_sid = msg["start"]["streamSid"]
                session = bot.register_session(call_sid, twilio_ws)
                if session is None:
                    print(f"[twilio] ERROR: unknown call_sid={call_sid}")
                    await twilio_ws.close()
                    return
                session.stream_sid = stream_sid
                session_ref.append(session)
                silence_task = asyncio.create_task(_silence_monitor(session))

            elif event == "media" and session_ref:
                session = session_ref[0]
                audio = b64_decode(msg["media"]["payload"])
                session.agent_audio_buf.extend(audio)
                await dg_ws.send(bytes(audio))
                session.is_agent_speaking = True
                session.last_audio_at = time.time()

            elif event == "stop":
                break
    finally:
        if silence_task:
            silence_task.cancel()
        if session_ref:
            session_ref[0].call_ended = True
        await dg_ws.close()


def _schedule_response(session: CallSession, t_agent_finished: float):
    asyncio.create_task(_bot_respond(session, t_agent_finished))


async def _receive_from_deepgram(dg_ws, session_ref: list):
    segments: list[str] = []  # speech_final-confirmed segments since last UtteranceEnd
    current_interim: str = ""  # latest in-progress interim text
    barge_in_fired: bool = False
    utterance_start_sec: float | None = None  # stream-relative start of current utterance
    async for raw in dg_ws:
        try:
            msg = json.loads(raw)
        except Exception:
            continue

        msg_type = msg.get("type")

        if msg_type == "Results":
            alts = msg.get("channel", {}).get("alternatives", [{}])
            text = alts[0].get("transcript", "").strip()
            if msg.get("is_final") and text:
                if utterance_start_sec is None:
                    words = alts[0].get("words", [])
                    if words and session_ref:
                        session = session_ref[0]
                        utterance_start_sec = words[0]["start"]
                        if session.t_bot_finished is not None:
                            t_next_agent_started = session.start_time + utterance_start_sec
                            for entry in reversed(session.turn_timestamps):
                                if "t_bot_finished" in entry and "t_next_agent_started" not in entry:
                                    entry["t_next_agent_started"] = t_next_agent_started
                                    break
                            session.t_bot_finished = None
                segments.append(text)
                current_interim = ""
                # Barge-in: on the first is_final segment of any interruption turn,
                # trigger an early response without waiting for UtteranceEnd.
                if (not barge_in_fired and session_ref and
                        session_ref[0].scenario.interruption_turns is not None and
                        session_ref[0].current_turn + 1 in session_ref[0].scenario.interruption_turns):
                    session = session_ref[0]
                    in_preamble = (utterance_start_sec is not None and
                                   utterance_start_sec < session.scenario.preamble_duration_sec)
                    if in_preamble:
                        partial_text = " ".join(segments)
                        segments = []
                        current_interim = ""
                        session.transcript.append({"role": "preamble", "text": partial_text, "ts": utterance_start_sec, "ts_end": None})
                        utterance_start_sec = None
                        print(f"[preamble-barge-in] {partial_text!r}")
                    else:
                        barge_in_fired = True
                        partial_text = " ".join(segments)
                        segments = []
                        current_interim = ""
                        t_agent_finished = time.monotonic()
                        session.transcript.append({"role": "agent", "text": partial_text, "ts": utterance_start_sec, "ts_end": None})
                        utterance_start_sec = None
                        session.conversation_history.append({"role": "user", "content": partial_text})
                        session.current_turn += 1
                        session.barge_in_start_ts = time.monotonic()
                        print(f"[agent-barge-in] {partial_text!r}")
                        _schedule_response(session, t_agent_finished)

            elif text:
                current_interim = text


        elif msg_type == "UtteranceEnd":
            parts = segments + ([current_interim] if current_interim else [])
            full_text = " ".join(parts)
            segments = []
            current_interim = ""

            if barge_in_fired:
                barge_in_fired = False
                if session_ref:
                    session = session_ref[0]
                    last_word_end = msg.get("last_word_end")
                    if last_word_end is not None:
                        if session.barge_in_start_ts is not None:
                            silence_onset = session.start_time + last_word_end
                            session.barge_in_ms_list.append((silence_onset - session.barge_in_start_ts) * 1000)
                            session.barge_in_start_ts = None
                        for entry in reversed(session.transcript):
                            if entry["role"] == "agent" and entry.get("ts_end") is None:
                                entry["ts_end"] = last_word_end
                                break
                utterance_start_sec = None
                continue

            if not full_text or not session_ref:
                utterance_start_sec = None
                continue
            session = session_ref[0]
            in_preamble = (utterance_start_sec is not None and
                           utterance_start_sec < session.scenario.preamble_duration_sec)
            if in_preamble:
                session.transcript.append({"role": "preamble", "text": full_text, "ts": utterance_start_sec, "ts_end": msg.get("last_word_end")})
                utterance_start_sec = None
                print(f"[preamble] {full_text!r}")
                continue
            last_word_end = msg.get("last_word_end")
            if last_word_end is not None:
                t_agent_finished = session.start_time + last_word_end
            else:
                t_agent_finished = time.monotonic() - UTTERANCE_END_MS / 1000
            session.transcript.append({"role": "agent", "text": full_text, "ts": utterance_start_sec, "ts_end": last_word_end})
            utterance_start_sec = None
            session.conversation_history.append({"role": "user", "content": full_text})
            session.current_turn += 1
            print(f"[agent] {full_text!r}")

            _schedule_response(session, t_agent_finished)


async def _stream_llm_to_tts(session: CallSession, t_agent_finished: float) -> tuple[str, float]:
    """Stream DeepSeek tokens into ElevenLabs WebSocket TTS concurrently."""
    el_url = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}/stream-input"
        "?model_id=eleven_turbo_v2&output_format=pcm_16000"
    )
    reply_parts: list[str] = []
    t_llm_done_box: list[float] = []
    t_first_audio_sent_box: list[float] = []
    first_audio = True
    ratecv_state = None
    prev_bot_len = len(session.bot_audio_buf)

    async with websockets.connect(el_url) as el_ws:
        await el_ws.send(json.dumps({
            "text": " ",
            "xi_api_key": settings.ELEVENLABS_API_KEY,
            "generation_config": {"chunk_length_schedule": [50]},
        }))

        async def produce():
            buf = ""
            llm_stream = await deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=session.conversation_history,
                stream=True,
            )
            async for chunk in llm_stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    reply_parts.append(token)
                    buf += token
                    if buf[-1] in _FLUSH_CHARS:
                        await el_ws.send(json.dumps({"text": buf}))
                        buf = ""
            if buf:
                await el_ws.send(json.dumps({"text": buf}))
            t_llm_done_box.append(time.monotonic())
            await el_ws.send(json.dumps({"text": ""}))

        async def consume():
            nonlocal first_audio, ratecv_state
            async for raw in el_ws:
                msg = json.loads(raw)
                audio_b64 = msg.get("audio")
                if audio_b64:
                    pcm16k = b64_decode(audio_b64)
                    if len(pcm16k) < 2:
                        continue
                    if len(pcm16k) % 2:
                        pcm16k = pcm16k[:-1]
                    if first_audio:
                        t_fas = time.monotonic()
                        t_first_audio_sent_box.append(t_fas)
                        session.turn_timestamps.append({
                            "t_agent_finished": t_agent_finished,
                            "t_first_audio_sent": t_fas,
                        })
                        first_audio = False
                    pcm8k, ratecv_state = audioop.ratecv(pcm16k, 2, 1, 16000, 8000, ratecv_state)
                    mulaw = audioop.lin2ulaw(pcm8k, 2)
                    session.bot_audio_buf.extend(pcm8k)
                    await session.twilio_ws.send_text(
                        json.dumps(make_media_event(session.stream_sid, b64_encode(mulaw)))
                    )
                if msg.get("isFinal"):
                    break

        await asyncio.gather(produce(), consume())

    if not first_audio:
        if t_llm_done_box:
            session.turn_timestamps[-1]["t_llm_done"] = t_llm_done_box[0]
        bot_audio_bytes = len(session.bot_audio_buf) - prev_bot_len
        t_bot_finished = t_first_audio_sent_box[0] + bot_audio_bytes / 16000
        session.turn_timestamps[-1]["t_bot_finished"] = t_bot_finished
        session.t_bot_finished = t_bot_finished
        session.bot_turn_offsets.append(len(session.bot_audio_buf))

    t_llm_done = t_llm_done_box[0] if t_llm_done_box else time.monotonic()
    return "".join(reply_parts), t_llm_done


async def _bot_respond(session: CallSession, t_agent_finished: float):
    try:
        await _bot_respond_inner(session, t_agent_finished)
    except Exception as e:
        print(f"[bot_respond] ERROR: {e!r}")


async def _bot_respond_inner(session: CallSession, t_agent_finished: float):
    async with session._bot_respond_lock:

        if await _conversation_is_over(session):
            goodbye = "Thank you, goodbye!"
            session.conversation_history.append({"role": "assistant", "content": goodbye})
            await _speak(session, goodbye, t_agent_finished)
            ts_entry = session.turn_timestamps[-1] if session.turn_timestamps else {}
            audio_start = ts_entry.get("t_first_audio_sent")
            audio_end = ts_entry.get("t_bot_finished")
            session.transcript.append({
                "role": "bot", "text": goodbye,
                "ts": round(audio_start - session.start_time, 3) if audio_start is not None else None,
                "ts_end": round(audio_end - session.start_time, 3) if audio_end is not None else None,
            })
            await _hang_up(session)
            return

        reply, _ = await _stream_llm_to_tts(session, t_agent_finished)
        reply = reply.strip()
        print(f"[bot] {reply!r}")
        session.conversation_history.append({"role": "assistant", "content": reply})
        ts_entry = session.turn_timestamps[-1] if session.turn_timestamps else {}
        audio_start = ts_entry.get("t_first_audio_sent")
        audio_end = ts_entry.get("t_bot_finished")
        session.transcript.append({
            "role": "bot", "text": reply,
            "ts": round(audio_start - session.start_time, 3) if audio_start is not None else None,
            "ts_end": round(audio_end - session.start_time, 3) if audio_end is not None else None,
        })

        bot_closing = ["goodbye", "bye", "take care", "have a great"]
        if any(phrase in reply.lower() for phrase in bot_closing):
            await _hang_up(session)
            return


async def _conversation_is_over(session: CallSession) -> bool:
    recent_agent = [t["text"].lower() for t in session.transcript[-4:] if t["role"] == "agent"]
    closing_phrases = [
        "goodbye", "bye", "have a good", "take care", "thank you for calling",
        "your appointment has been", "we'll see you", "see you then",
        "you're all set for your appointment", "all set for your",
        "is there anything else i can help",
    ]
    keyword_hit = any(phrase in turn for turn in recent_agent for phrase in closing_phrases)
    if not keyword_hit:
        return False
    return await _llm_goal_check(session)


async def _llm_goal_check(session: CallSession) -> bool:
    transcript_text = "\n".join(
        f"{t['role'].upper()}: {t['text']}" for t in session.transcript
    )
    prompt = (
        f"Scenario goal: {session.scenario.edge_case_notes}\n\n"
        f"Transcript:\n{transcript_text}\n\n"
        "Has the conversation reached a natural end? Reply with only YES or NO."
    )
    resp = await deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5,
    )
    return resp.choices[0].message.content.strip().upper().startswith("YES")


async def _speak(session: CallSession, text: str, t_agent_finished: float, t_llm_done: float | None = None):
    print(f"[bot] {text!r}")
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}/stream"
        "?output_format=pcm_16000"
    )
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
    }

    first_chunk = True
    ratecv_state = None
    prev_bot_len = len(session.bot_audio_buf)
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes(chunk_size=640):  # 640 bytes = 20ms at 16kHz PCM16
                if not chunk or len(chunk) < 2:
                    continue
                # Ensure even byte count for PCM16
                if len(chunk) % 2:
                    chunk = chunk[:-1]
                if first_chunk:
                    t_first_audio_sent = time.monotonic()
                    entry: dict = {
                        "t_agent_finished": t_agent_finished,
                        "t_first_audio_sent": t_first_audio_sent,
                    }
                    if t_llm_done is not None:
                        entry["t_llm_done"] = t_llm_done
                    session.turn_timestamps.append(entry)
                    first_chunk = False
                # Downsample 16kHz → 8kHz, then encode to G.711 μ-law for Twilio
                pcm8k, ratecv_state = audioop.ratecv(chunk, 2, 1, 16000, 8000, ratecv_state)
                mulaw_chunk = audioop.lin2ulaw(pcm8k, 2)
                session.bot_audio_buf.extend(pcm8k)  # store 8kHz PCM for WAV
                await session.twilio_ws.send_text(
                    json.dumps(make_media_event(session.stream_sid, b64_encode(mulaw_chunk)))
                )
    if not first_chunk:
        bot_audio_bytes = len(session.bot_audio_buf) - prev_bot_len
        t_bot_finished = t_first_audio_sent + bot_audio_bytes / 16000
        session.turn_timestamps[-1]["t_bot_finished"] = t_bot_finished
        session.t_bot_finished = t_bot_finished
        session.bot_turn_offsets.append(len(session.bot_audio_buf))


async def _hang_up(session: CallSession):
    bot._twilio.calls(session.call_sid).update(status="completed")


async def _cleanup(session: CallSession):
    Path("transcripts").mkdir(exist_ok=True)
    transcript_path = Path("transcripts") / f"{session.scenario.id}.json"
    transcript_path.write_text(json.dumps({
        "scenario_id": session.scenario.id,
        "transcript": session.transcript,
        "turn_timestamps": session.turn_timestamps,
    }, indent=2))

    if session.agent_audio_buf and session.bot_audio_buf:
        combine_recordings(
            session.scenario.id,
            bytes(session.agent_audio_buf),
            bytes(session.bot_audio_buf),
            session.bot_turn_offsets,
            session.turn_timestamps,
            session.start_time,
        )

    bot.resolve_session(session.call_sid, CallResult(
        scenario_id=session.scenario.id,
        transcript=session.transcript,
        turn_timestamps=session.turn_timestamps,
        barge_in_ms_list=session.barge_in_ms_list,
    ))
