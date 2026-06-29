import base64
import struct
import wave
from pathlib import Path


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def b64_decode(data: str) -> bytes:
    return base64.b64decode(data)


def make_media_event(stream_sid: str, b64_audio: str) -> dict:
    return {
        "event": "media",
        "streamSid": stream_sid,
        "media": {"payload": b64_audio},
    }


def make_clear_event(stream_sid: str) -> dict:
    return {"event": "clear", "streamSid": stream_sid}


def mulaw_to_pcm16(mulaw_bytes: bytes) -> bytes:
    """Convert 8-bit mulaw samples to 16-bit linear PCM."""
    pcm = bytearray(len(mulaw_bytes) * 2)
    for i, byte in enumerate(mulaw_bytes):
        # ITU-T G.711 mulaw decode
        byte = ~byte & 0xFF
        sign = byte & 0x80
        exponent = (byte >> 4) & 0x07
        mantissa = byte & 0x0F
        sample = ((mantissa << 1) | 0x21) << exponent
        sample -= 33
        if sign:
            sample = -sample
        # clamp to int16
        sample = max(-32768, min(32767, sample))
        pcm[i * 2] = sample & 0xFF
        pcm[i * 2 + 1] = (sample >> 8) & 0xFF
    return bytes(pcm)


def _mix_into(base: bytearray, overlay: bytes, offset_bytes: int) -> None:
    """Mix overlay PCM16-LE samples into base at offset_bytes, clamping to int16."""
    end = min(offset_bytes + len(overlay), len(base))
    for pos in range(offset_bytes, end, 2):
        i = pos - offset_bytes
        if i + 2 > len(overlay):
            break
        a = struct.unpack_from("<h", base, pos)[0]
        b = struct.unpack_from("<h", overlay, i)[0]
        struct.pack_into("<h", base, pos, max(-32768, min(32767, a + b)))


def combine_recordings(
    scenario_id: str,
    agent_mulaw: bytes,
    bot_pcm: bytes,
    bot_turn_offsets: list[int],
    turn_timestamps: list[dict],
    session_start: float,
) -> Path:
    agent_pcm = mulaw_to_pcm16(agent_mulaw)
    combined = bytearray(agent_pcm)

    prev_offset = 0
    next_available_byte = 0
    for ts, end_offset in zip(turn_timestamps, bot_turn_offsets):
        if "t_first_audio_sent" not in ts:
            prev_offset = end_offset
            continue
        t_based_start = int((ts["t_first_audio_sent"] - session_start) * 8000) * 2
        start_byte = max(t_based_start, next_available_byte)
        bot_segment = bot_pcm[prev_offset:end_offset]
        needed = start_byte + len(bot_segment)
        if needed > len(combined):
            combined.extend(bytes(needed - len(combined)))
        _mix_into(combined, bot_segment, start_byte)
        next_available_byte = start_byte + len(bot_segment)
        prev_offset = end_offset

    recordings_dir = Path("recordings")
    recordings_dir.mkdir(exist_ok=True)
    wav_path = recordings_dir / f"{scenario_id}_combined.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(bytes(combined))
    return wav_path


def save_recording(call_id: str, audio_bytes: bytes, already_pcm: bool = False) -> Path:
    recordings_dir = Path("recordings")
    recordings_dir.mkdir(exist_ok=True)

    wav_path = recordings_dir / f"{call_id}.wav"
    pcm = audio_bytes if already_pcm else mulaw_to_pcm16(audio_bytes)

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(8000)
        wf.writeframes(pcm)

    return wav_path
