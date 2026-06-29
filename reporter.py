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
    avg_barge_in_ms: float | None
    max_barge_in_ms: float | None

    # Task layer (LLM-extracted, verbatim)
    patient_primary_intent: str | None
    agent_primary_action: str | None
    task_completed: bool
    outcome_correct: bool | None
    mismatch_excerpt: str | None
    redundant_repeats: int

    # Efficiency layer
    turns_to_completion: int
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
        "  redundant_repeats: integer count of times the agent asked for information the patient had already clearly provided. "
        "Only count cases where the patient gave a direct, complete answer and the agent asked for the exact same information again without a valid reason "
        "(e.g. agent asks for date of birth twice after patient already stated it). Do not count clarifying follow-ups or cases where the patient's answer was vague or incomplete.\n"
        "Return only the JSON object, no commentary."
    )
    resp = sync_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)



def _efficiency(turn_timestamps: list[dict]) -> tuple[int, float | None, float | None]:
    if not turn_timestamps:
        return 0, None, None
    agent_latencies = [
        (ts["t_next_agent_started"] - ts["t_bot_finished"]) * 1000
        for ts in turn_timestamps
        if "t_bot_finished" in ts and "t_next_agent_started" in ts
        and ts["t_next_agent_started"] > ts["t_bot_finished"]
    ]
    avg_agent = mean(agent_latencies) if agent_latencies else None
    max_agent = max(agent_latencies) if agent_latencies else None
    return len(turn_timestamps), avg_agent, max_agent


def build_scenario_result(call_result: CallResult, scenario_name: str, edge_case_notes: str) -> ScenarioResult:
    task = _extract_task_layer(call_result, scenario_name, edge_case_notes)
    turns, avg_agent_lat, max_agent_lat = _efficiency(call_result.turn_timestamps)
    bi = call_result.barge_in_ms_list
    avg_barge_in = mean(bi) if bi else None
    max_barge_in = max(bi) if bi else None

    return ScenarioResult(
        scenario_id=call_result.scenario_id,
        scenario_name=scenario_name,
        edge_case_notes=edge_case_notes,
        transcript=call_result.transcript,
        turn_timestamps=call_result.turn_timestamps,
        patient_primary_intent=task.get("patient_primary_intent"),
        agent_primary_action=task.get("agent_primary_action"),
        task_completed=bool(task.get("task_completed")),
        outcome_correct=task.get("outcome_correct"),
        mismatch_excerpt=task.get("mismatch_excerpt"),
        redundant_repeats=int(task.get("redundant_repeats") or 0),
        turns_to_completion=turns,
        avg_agent_response_ms=avg_agent_lat,
        max_agent_response_ms=max_agent_lat,
        avg_barge_in_ms=avg_barge_in,
        max_barge_in_ms=max_barge_in,
    )


def _render_report(results: list[ScenarioResult]) -> str:
    lines = ["# Vocaline Caller Bot — Bug Report\n"]

    lines.append("## Summary\n")
    lines.append("| Scenario | Task Done | Outcome OK | Redundant Repeats | Avg Agent Resp (ms) | Max Agent Resp (ms) | Avg Barge-in (ms) | Max Barge-in (ms) | Rounds |")
    lines.append("|----------|-----------|------------|-------------------|---------------------|---------------------|-------------------|-------------------|--------|")
    for r in results:
        outcome = ("✓" if r.outcome_correct else "✗") if r.outcome_correct is not None else "—"
        avg_agent = f"{r.avg_agent_response_ms:.0f}" if r.avg_agent_response_ms is not None else "—"
        max_agent = f"{r.max_agent_response_ms:.0f}" if r.max_agent_response_ms is not None else "—"
        avg_bi = f"{r.avg_barge_in_ms:.0f}" if r.avg_barge_in_ms is not None else "—"
        max_bi = f"{r.max_barge_in_ms:.0f}" if r.max_barge_in_ms is not None else "—"
        lines.append(
            f"| {r.scenario_name} "
            f"| {'✓' if r.task_completed else '✗'} "
            f"| {outcome} "
            f"| {r.redundant_repeats} "
            f"| {avg_agent} "
            f"| {max_agent} "
            f"| {avg_bi} "
            f"| {max_bi} "
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
        lines.append(f"**Redundant repeats:** {r.redundant_repeats}  ")
        lines.append(f"**Rounds:** {r.turns_to_completion}  ")
        if r.avg_agent_response_ms is not None:
            lines.append(f"**Avg agent response:** {r.avg_agent_response_ms:.0f} ms  ")
            lines.append(f"**Max agent response:** {r.max_agent_response_ms:.0f} ms  ")
        if r.avg_barge_in_ms is not None:
            lines.append(f"**Avg barge-in yield time:** {r.avg_barge_in_ms:.0f} ms  ")
            lines.append(f"**Max barge-in yield time:** {r.max_barge_in_ms:.0f} ms  ")

        lines.append("\n**Patient primary intent:** " + (r.patient_primary_intent or "—"))
        lines.append("\n**Agent primary action:** " + (r.agent_primary_action or "—"))

        lines.append("\n### Per-round agent response\n")
        lines.append("| Round | Agent Resp (ms) | Note |")
        lines.append("|-------|-----------------|------|")
        for i, ts in enumerate(r.turn_timestamps, 1):
            has_times = "t_bot_finished" in ts and "t_next_agent_started" in ts
            if has_times:
                delta = (ts["t_next_agent_started"] - ts["t_bot_finished"]) * 1000
                if delta > 0:
                    agent_ms, note = f"{delta:.0f}", ""
                else:
                    agent_ms, note = "—", "barge-in"
            else:
                agent_ms, note = "—", ""
            lines.append(f"| {i} | {agent_ms} | {note} |")

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
