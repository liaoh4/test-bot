import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import openai

from caller_bot import CallResult
from config import settings

sync_client = openai.OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


@dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    edge_case_notes: str
    transcript: list[dict]
    turn_timestamps: list[dict]
    observed_response_ms: float | None

    # Task layer (LLM-extracted, verbatim)
    patient_primary_intent: str | None
    agent_primary_action: str | None
    task_completed: bool
    outcome_correct: bool | None
    mismatch_excerpt: str | None

    # Efficiency layer
    turns_to_completion: int
    avg_response_latency_ms: float
    max_response_latency_ms: float
    avg_llm_latency_ms: float | None
    max_llm_latency_ms: float | None
    avg_tts_latency_ms: float | None
    max_tts_latency_ms: float | None
    avg_agent_response_ms: float | None
    max_agent_response_ms: float | None


def _extract_task_layer(result: CallResult, scenario_name: str, edge_case_notes: str) -> dict:
    transcript_text = "\n".join(
        f"{t['role'].upper()}: {t['text']}" for t in result.transcript
    )
    prompt = (
        f"Scenario: {scenario_name}\nNotes: {edge_case_notes}\n\n"
        f"Transcript:\n{transcript_text}\n\n"
        "Extract the following fields from the transcript.\n"
        "Return JSON with these keys:\n"
        "  patient_primary_intent: what the patient is trying to accomplish (e.g. appointment type, timing, provider preference)\n"
        "  agent_primary_action: the main action the agent took (e.g. \"Booked a general checkup with Dr. Chen on Tuesday June 30 at 9AM\", or \"Escalated to human assistant\", or \"Transferred call to billing team\"). Never null — always describe what the agent did, even if it was refusing, escalating, or failing to act.\n"
        "  task_completed: true if the agent successfully completed the task described in the scenario notes, false otherwise\n"
        "  outcome_correct: true if the agent's action matches what the scenario notes say is the correct outcome, false if not, null only if the transcript is too ambiguous to judge\n"
        "  mismatch_excerpt: the agent line that best shows the mismatch or failure, or null\n"
        "Return only the JSON object, no commentary."
    )
    resp = sync_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)



def _efficiency(turn_timestamps: list[dict]) -> tuple[
    int, float, float,
    float | None, float | None,
    float | None, float | None,
    float | None, float | None,
]:
    if not turn_timestamps:
        return 0, 0.0, 0.0, None, None, None, None, None, None
    bot_latencies = [
        (ts["t_first_audio_sent"] - ts["t_agent_finished"]) * 1000
        for ts in turn_timestamps
    ]
    llm_latencies = [
        (ts["t_llm_done"] - ts["t_agent_finished"]) * 1000
        for ts in turn_timestamps
        if "t_llm_done" in ts
    ]
    tts_latencies = [
        (ts["t_first_audio_sent"] - ts["t_llm_done"]) * 1000
        for ts in turn_timestamps
        if "t_llm_done" in ts
    ]
    agent_latencies = [
        (ts["t_next_agent_started"] - ts["t_bot_finished"]) * 1000
        for ts in turn_timestamps
        if "t_bot_finished" in ts and "t_next_agent_started" in ts
    ]
    avg_llm = mean(llm_latencies) if llm_latencies else None
    max_llm = max(llm_latencies) if llm_latencies else None
    avg_tts = mean(tts_latencies) if tts_latencies else None
    max_tts = max(tts_latencies) if tts_latencies else None
    avg_agent = mean(agent_latencies) if agent_latencies else None
    max_agent = max(agent_latencies) if agent_latencies else None
    return len(bot_latencies), mean(bot_latencies), max(bot_latencies), avg_llm, max_llm, avg_tts, max_tts, avg_agent, max_agent


def build_scenario_result(call_result: CallResult, scenario_name: str, edge_case_notes: str) -> ScenarioResult:
    task = _extract_task_layer(call_result, scenario_name, edge_case_notes)
    agent_primary_action = task.get("agent_primary_action")
    turns, avg_lat, max_lat, avg_llm, max_llm, avg_tts, max_tts, avg_agent_lat, max_agent_lat = _efficiency(call_result.turn_timestamps)

    return ScenarioResult(
        scenario_id=call_result.scenario_id,
        scenario_name=scenario_name,
        edge_case_notes=edge_case_notes,
        transcript=call_result.transcript,
        turn_timestamps=call_result.turn_timestamps,
        observed_response_ms=call_result.observed_response_ms,
        patient_primary_intent=task.get("patient_primary_intent"),
        agent_primary_action=agent_primary_action,
        task_completed=bool(task.get("task_completed")),
        outcome_correct=task.get("outcome_correct"),
        mismatch_excerpt=task.get("mismatch_excerpt"),
        turns_to_completion=turns,
        avg_response_latency_ms=avg_lat,
        max_response_latency_ms=max_lat,
        avg_llm_latency_ms=avg_llm,
        max_llm_latency_ms=max_llm,
        avg_tts_latency_ms=avg_tts,
        max_tts_latency_ms=max_tts,
        avg_agent_response_ms=avg_agent_lat,
        max_agent_response_ms=max_agent_lat,
    )


def _render_report(results: list[ScenarioResult]) -> str:
    lines = ["# Vocaline Caller Bot — Bug Report\n"]

    lines.append("## Summary\n")
    lines.append("| Scenario | Task Done | Outcome OK | Avg Bot Resp (ms) | Max Bot Resp (ms) | Avg LLM (ms) | Max LLM (ms) | Avg TTS (ms) | Max TTS (ms) | Avg Agent Resp (ms) | Max Agent Resp (ms) | Barge-in (ms) | Rounds |")
    lines.append("|----------|-----------|------------|-------------------|-------------------|--------------|--------------|--------------|--------------|---------------------|---------------------|---------------|--------|")
    for r in results:
        outcome = ("✓" if r.outcome_correct else "✗") if r.outcome_correct is not None else "—"
        avg_llm = f"{r.avg_llm_latency_ms:.0f}" if r.avg_llm_latency_ms is not None else "—"
        max_llm = f"{r.max_llm_latency_ms:.0f}" if r.max_llm_latency_ms is not None else "—"
        avg_tts = f"{r.avg_tts_latency_ms:.0f}" if r.avg_tts_latency_ms is not None else "—"
        max_tts = f"{r.max_tts_latency_ms:.0f}" if r.max_tts_latency_ms is not None else "—"
        avg_agent = f"{r.avg_agent_response_ms:.0f}" if r.avg_agent_response_ms is not None else "—"
        max_agent = f"{r.max_agent_response_ms:.0f}" if r.max_agent_response_ms is not None else "—"
        barge_in = f"{r.observed_response_ms:.0f}" if r.observed_response_ms is not None else "—"
        lines.append(
            f"| {r.scenario_name} "
            f"| {'✓' if r.task_completed else '✗'} "
            f"| {outcome} "
            f"| {r.avg_response_latency_ms:.0f} "
            f"| {r.max_response_latency_ms:.0f} "
            f"| {avg_llm} "
            f"| {max_llm} "
            f"| {avg_tts} "
            f"| {max_tts} "
            f"| {avg_agent} "
            f"| {max_agent} "
            f"| {barge_in} "
            f"| {r.turns_to_completion} |"
        )

    for r in results:
        lines.append(f"\n---\n\n## {r.scenario_name}\n")
        lines.append(f"**Scenario ID:** `{r.scenario_id}`  ")
        lines.append(f"**Notes:** {r.edge_case_notes}\n")
        lines.append(f"**Task completed:** {'Yes' if r.task_completed else 'No'}  ")
        outcome_str = ("Yes" if r.outcome_correct else "No") if r.outcome_correct is not None else "N/A"
        lines.append(f"**Outcome correct:** {outcome_str}  ")
        if r.mismatch_excerpt:
            lines.append(f"**Mismatch:** > {r.mismatch_excerpt}  ")
        lines.append(f"**Rounds:** {r.turns_to_completion}  ")
        lines.append(f"**Avg bot response:** {r.avg_response_latency_ms:.0f} ms  ")
        lines.append(f"**Max bot response:** {r.max_response_latency_ms:.0f} ms  ")
        if r.avg_llm_latency_ms is not None:
            lines.append(f"**Avg LLM latency:** {r.avg_llm_latency_ms:.0f} ms  ")
            lines.append(f"**Max LLM latency:** {r.max_llm_latency_ms:.0f} ms  ")
        if r.avg_tts_latency_ms is not None:
            lines.append(f"**Avg TTS latency:** {r.avg_tts_latency_ms:.0f} ms  ")
            lines.append(f"**Max TTS latency:** {r.max_tts_latency_ms:.0f} ms  ")
        if r.avg_agent_response_ms is not None:
            lines.append(f"**Avg agent response:** {r.avg_agent_response_ms:.0f} ms  ")
            lines.append(f"**Max agent response:** {r.max_agent_response_ms:.0f} ms  ")
        if r.observed_response_ms is not None:
            lines.append(f"**Barge-in response time:** {r.observed_response_ms:.0f} ms  ")

        lines.append("\n**Patient primary intent:** " + (r.patient_primary_intent or "—"))
        lines.append("\n**Agent primary action:** " + (r.agent_primary_action or "—"))

        lines.append("\n### Per-round latency\n")
        lines.append("| Round | Bot Resp (ms) | LLM (ms) | TTS (ms) | Agent Resp (ms) |")
        lines.append("|-------|--------------|----------|----------|-----------------|")
        for i, ts in enumerate(r.turn_timestamps, 1):
            bot_ms = f"{(ts['t_first_audio_sent'] - ts['t_agent_finished']) * 1000:.0f}"
            llm_ms = (
                f"{(ts['t_llm_done'] - ts['t_agent_finished']) * 1000:.0f}"
                if "t_llm_done" in ts else "—"
            )
            tts_ms = (
                f"{(ts['t_first_audio_sent'] - ts['t_llm_done']) * 1000:.0f}"
                if "t_llm_done" in ts else "—"
            )
            agent_ms = (
                f"{(ts['t_next_agent_started'] - ts['t_bot_finished']) * 1000:.0f}"
                if "t_bot_finished" in ts and "t_next_agent_started" in ts
                else "—"
            )
            lines.append(f"| {i} | {bot_ms} | {llm_ms} | {tts_ms} | {agent_ms} |")

        lines.append("\n<details><summary>Transcript</summary>\n")
        for turn in r.transcript:
            lines.append(f"**{turn['role'].upper()}:** {turn['text']}\n")
        lines.append("</details>")

    return "\n".join(lines)


def generate_report(call_results: list[CallResult]) -> Path:
    from scenarios import ALL_SCENARIOS
    scenario_map = {s.id: s for s in ALL_SCENARIOS}

    results = []
    for cr in call_results:
        scenario = scenario_map.get(cr.scenario_id)
        name = scenario.name if scenario else cr.scenario_id
        notes = scenario.edge_case_notes if scenario else ""
        results.append(build_scenario_result(cr, name, notes))

    if len(results) == 1:
        report_path = Path(f"bug_report_{results[0].scenario_id}.md")
    else:
        report_path = Path("bug_report.md")

    report_path.write_text(_render_report(results))
    return report_path
