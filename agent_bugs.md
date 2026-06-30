# Agent Bug Analysis

| ID | Severity | Scenario(s) | Description |
|----|----------|-------------|-------------|
| BUG-01 | Critical | `happy_path_booking` | Agent never offered alternative slots when preferred days unavailable; gave up and transferred to dead line |
| BUG-02 | High | `role_consistency` | Answers off-topic questions instead of redirecting; no consistent role boundary |
| BUG-03 | High | `unclear_request`, `intent_recovery`, `happy_path_booking` | Latency spikes up to 31.78s (ts 157.3s–189.1s) with no hold acknowledgment |
| BUG-04 | High | `role_consistency` (9/16 turns), `weekend_appointment` (4/10 turns) | Agent fires on every STT `is_final` signal; barge-ins up to 7.3s early on long patient turns |
| BUG-05 | High | `barge_in_test` | Agent ignores patient barge-in; continues speaking 11.65s after interruption (ts 93.44s–105.93s) |
| BUG-06 | High | All scenarios | Agent audio ~11 dB below telephony standard (peak -14.5 dBFS vs target -3 to 0 dBFS) |
| BUG-07 | High | `intent_recovery` | Agent transfers call without patient consent; patient's objection ignored |
| BUG-08 | High | `multilingual` | No bilingual support; Spanish input causes missed DOB, repeated questions, and false English-only declaration |
| BUG-09 | High | `unclear_request` | Open slots existed but agent reported none; likely misidentified visit reason |
| BUG-10 | Medium | `intent_recovery` | Duplicate new patient consultation rule not communicated; no alternatives offered before escalation |
| BUG-11 | Medium | `role_consistency` | Contradictory availability info within same call |
| BUG-12 | Medium | `weekend_appointment`, `multilingual` | Text confirmation offer missing after successful booking |
| BUG-13 | Medium | `medication_refill` | Agent resumes 1.17s after "hold on"; patient's acknowledgment barged in on (ts 179.18s–192.05s) |

---

## Critical

### BUG-01 — Agent Fails to Offer Alternatives When Patient's Preferred Slot Is Unavailable
**Scenario:** `happy_path_booking`

The patient expressed a soft preference for Monday or Tuesday. Each time the agent found no availability on those days, it simply confirmed the absence and asked the patient to redirect — putting the burden back on the patient every round. The agent never proactively offered an alternative slot. After three weeks of Mon/Tue searches with no results, the agent gave up and transferred the patient to support, which hit the dead test line and ended the call.

`role_consistency` ran the same general checkup appointment type and successfully booked a slot, confirming the appointment type itself is not broken. The failure in `happy_path_booking` is that the agent passively followed the patient's narrowing preference without ever suggesting alternatives:

> Instead of: *"There's nothing on Monday or Tuesday — would you like me to keep checking those days?"*
> The agent should say: *"I don't see Monday or Tuesday, but I do have Thursday the 9th at 1:30PM — would that work for you?"*

When a preferred slot is unavailable, the agent should proactively surface the nearest available alternative rather than waiting for the patient to redirect the search.

---

## High

### BUG-02 — Role Adherence Failure Under Off-Topic Pressure
**Scenario:** `role_consistency`

The agent answered multiple off-topic questions it should have deflected:
- Steph Curry GOAT debate → *"Nope."* (terse, breaks character)
- Follow-up basketball question → gave a full opinion on Magic Johnson vs. Curry vs. Stockton
- Pizza topping question → gave a personal opinion on pepperoni and mushrooms
- Poem request → wrote and recited a scheduling poem

The agent has no consistent policy for handling off-topic pressure — responses ranged from a one-word dismissal to a full essay to a poem, depending on how the patient phrased the request. This is unpredictable at scale and poses professionalism and liability risks in a healthcare context.


---

### BUG-03 — Severe Latency Spikes Leave Patient in Silence
**Scenarios:** `unclear_request` (31,782 ms), `intent_recovery` (16,301 ms), `happy_path_booking` (8,392 ms)

The agent produces multi-second silences with no acknowledgment while performing backend searches. The worst instance is in `unclear_request`: after the bot said *"You search for me, please. Later in week is okay. I wait. Just tell me what day and time."*, the agent went silent for **31.78 seconds** before responding.

**Timestamps (call-relative, `unclear_request`):**
- Bot finished speaking: `ts_end = 157.288s`
- Agent started responding: `ts = 189.07s`
- **Silence gap: 31.782 seconds**

From a patient's perspective a silence this long is indistinguishable from a dropped call. The agent should send an interim acknowledgment ("One moment while I search for you…") before initiating any long backend query.

---

### BUG-04 — Agent Barge-ins When Client is Speaking
**Scenarios:** `role_consistency` (primary — 9/16 turns), `weekend_appointment` (4/10 turns)

Barge-ins were observed in multiple scenarios. The agent repeatedly starts responding before the patient has finished speaking. Barge-in counts are highest on longer patient utterances

**Hypothesized root causes (two candidates):**

1. **`is_final` trigger** — The agent triggers a response immediately on every `is_final` signal from the STT engine. In real-time STT, `is_final: true` is sent when the engine commits to a transcription segment — not necessarily because the speaker has stopped, but because it detected a natural phrase boundary or a brief inter-clause pause. Acting on every `is_final` causes the agent to barge in mid-sentence while the patient is still phonating.

2. **Silence detection threshold too short** — The agent's end-of-utterance silence window may be set too low. A natural mid-sentence pause (breath, clause boundary) exceeds the threshold, triggering an end-of-utterance signal before the patient resumes. The agent fires during a genuine brief pause rather than at a phrase boundary.

Both hypotheses predict more barge-ins on longer turns (more phrase boundaries *and* more natural pauses), so the symptom data alone doesn't distinguish them. The barge-in timing relative to audio would: if the agent fires while the patient is still phonating, it's hypothesis 1; if it fires during a silent gap before the patient resumes, it's hypothesis 2.

**Downstream consequences:**
- **Rescheduling reason asked twice** (`rescheduling`, `barge_in_test`) — the agent barged in mid-answer, missed the patient's response, and re-prompted.
- **DOB asked twice** (multiple scenarios) — the agent cut off the patient mid-DOB (e.g., before "2000" in "July 4th, 2000"), received an incomplete value, and re-asked. Same root cause.

---

### BUG-05 — Agent Does Not Stop Speaking When Patient Barge-in is Detected
**Scenario:** `barge_in_test`

When the patient interrupts the agent mid-speech, the agent fails to yield and continues playing its full response. Timestamp analysis of the critical exchange:

- Agent started speaking: `ts 93.44s`
- Bot barged in: `ts 94.281s` (0.84s into agent's turn)
- Bot finished: `ts_end 97.439s`
- Agent finally stopped: `ts_end 105.93s`

The agent kept talking for **11.65 seconds after the patient started speaking**, and **8.49 seconds after the patient had already finished**. The patient's input was effectively ignored during this window, creating a confusing overlap where both sides were speaking simultaneously.

This is distinct from BUG-04 (agent fires too early and cuts off the patient). Here the direction is reversed: the patient interrupts the agent, but the agent has no mechanism to detect the interruption and stop its own audio output mid-stream. The agent should cut off its current playback as soon as it detects patient speech.

---

### BUG-06 — Agent Audio Volume Too Low Across All Scenarios
**Scenarios:** All

The agent's output audio is consistently too quiet across every recorded scenario, and at times is barely audible. Volume analysis on two separate recordings confirms the issue is not scenario-specific but a fixed configuration problem on the agent's side:

| Recording | Agent mean | Agent peak | Bot mean | Bot peak |
|-----------|-----------|------------|----------|----------|
| `happy_path_booking` | -34.1 dBFS | -14.4 dBFS | -27.5 dBFS | -1.1 dBFS |
| `weekend_appointment` | -34.6 dBFS | -14.7 dBFS | -26.6 dBFS | -0.3 dBFS |

The agent's peak is consistently around **-14.5 dBFS** — approximately **11 dB below** the normal telephony target of -3 to 0 dBFS. The near-identical values across both recordings strongly suggest a hardcoded gain setting rather than a transient issue.

For reference, normal telephony voice targets:
- Mean: -18 to -12 dBFS
- Peak: -3 to 0 dBFS

---

### BUG-07 — Agent Transfers Call Without Patient Confirmation
**Scenario:** `intent_recovery`

When the agent decided to escalate to live support, it transferred the call immediately without asking the patient's consent. The patient was mid-conversation and not willing to be transferred:

> **AGENT:** It looks like there's a conflict with your appointment status, so I'll connect you to our patient support team to help get this sorted out. Please stay on the line. Connecting you to a representative...

The patient tried to intervene — *"Wait, before you transfer me..."* — but was already being connected. Compare this to `happy_path_booking`, where the agent correctly asked first: *"I can connect you to our patient support team for more help. Would you like me to transfer you?"* The confirmation step is inconsistently applied. Transfers should always require explicit patient consent before initiating.

---

### BUG-08 — No Bilingual Support; Mixed-Language Input Causes Repeated Questions and Missed Data
**Scenario:** `multilingual`

The agent does not support bilingual conversations. When the patient switched between English and Spanish, several downstream failures occurred — all sharing the same root cause:

- **Declared English-only** — When the patient said she was bilingual and would switch languages, the agent responded: *"You can continue in English. As I will respond in English only."* — yet it understood Spanish input throughout the call, making this restriction both unnecessary and misleading.
- **DOB year not captured in mixed input** — After the patient said *"Mi fecha de nacimiento es July fourth, two thousand"*, the agent captured the month and day but missed the year, asking: *"Can you tell me the year you were born as well?"*
- **Visit reason asked twice** — The patient described knee pain in mixed English/Spanish. The agent failed to extract the visit reason and re-asked, adding an unnecessary round.
- **Provider preference asked twice** — The patient clearly stated *"El primer disponible está bien para mí"* (first available is fine). The agent asked again for clarification on provider preference.

All four symptoms point to the same issue: the agent's intent extraction and slot-filling logic breaks down when input contains Spanish. The scenario outcome was still correct, but only because the patient was cooperative and persistent enough to repeat herself.

---

### BUG-09 — Open Slots Existed But Agent Reported None
**Scenario:** `unclear_request`

The agent initially confirmed availability: *"We have openings this week and early next week."* However, when the patient's preferences narrowed to "any day after Wednesday," the agent returned no results and ultimately gave up: *"I am not finding any open appointments even looking far ahead."* `weekend_appointment`, which ran immediately after, found Thursday July 9 slots without difficulty — slots that should have been available during `unclear_request` as well.

One possible reason is that the agent didn't correctly identify the patient's visit reason from vague, mixed-language input, so it didn't know how to search for the right appointment type. Having confirmed availability at the start but then failing to retrieve it, the agent effectively lost track of what it was searching for as the conversation progressed.

---

## Medium

### BUG-10 — Duplicate New Patient Consultation Rule Not Explained to Patient
**Scenario:** `intent_recovery`

When the patient tried to book a new consultation, the agent detected an existing appointment from a prior scenario (`weekend_appointment`) and responded: *"It looks like you already have a new patient consultation appointment booked."* The one-active-new-patient-consultation rule appears to be an intentional and consistently applied business constraint — other appointment types (urgent visits, general checkups) were not blocked. However, the agent handled it poorly: it did not explain the policy to the patient, and escalated directly to live support without the patient's consent — resulting in a hang-up. The agent should clearly explain why a new booking is blocked and present the patient with actionable alternatives (reschedule, cancel existing, or speak to a representative).

---

### BUG-11 — Contradictory Availability Within Same Call
**Scenario:** `role_consistency`

The agent stated *"no openings through July 23"* then, in the very next search, offered July 8 slots. The patient called this out and the agent acknowledged the inconsistency. The contradiction appears to be caused by different search parameters (provider filter changed), but the agent presents results as if they are comparable, which undermines trust.

---

### BUG-12 — Text Confirmation Offer Missing in Some Booking Scenarios
**Scenarios:** `weekend_appointment` (confirmed missing); `multilingual` (ambiguous — agent was cut off mid-confirmation)

After successfully booking an appointment, the agent inconsistently offers to send a text message with the appointment details. It is present in `rescheduling`, `barge_in_test`, and `role_consistency`, but absent in `weekend_appointment`, where the agent ends with *"Is there anything else you need?"* instead.

If sending a text confirmation is a standard post-booking step, it should be offered consistently at the end of every successful booking regardless of scenario. Skipping it in some calls means patients may leave without a written record of their appointment details.

---

### BUG-13 — Agent Resumes Speaking Immediately After "Hold On", Causing Overlap
**Scenario:** `medication_refill`

The agent said *"Please hold on. Your refill request is—"* then resumed with the result only **1.17 seconds later**, before the patient had any time to acknowledge the hold. The patient naturally replied *"Thank you, I appreciate it. I'll wait."* at `ts 181.936s`, but by then the agent had already been speaking for 2.76 seconds and continued through `ts_end 192.05s`, talking over the patient's entire response.

**Timestamps:**
- Agent "hold on": `ts 171.04s – 178.01s`
- Agent resumed with result: `ts 179.18s` (1.17s gap)
- Bot replied "I'll wait": `ts 181.936s – 184.676s`
- Agent finished result: `ts_end 192.05s`

The "hold on" prompt creates an expectation of a meaningful pause, but the agent's near-instant return makes it effectively false. The agent should either skip the "hold on" if the tool call is already resolved, or wait long enough after resuming for the patient to acknowledge before continuing.

