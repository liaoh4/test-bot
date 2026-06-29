from dataclasses import dataclass


@dataclass
class Scenario:
    id: str
    name: str
    persona_prompt: str        # may contain {patient_name} and {patient_dob} placeholders
    edge_case_notes: str
    interruption_turns: list[int] | None = None
    max_duration_sec: int = 240
    preamble_duration_sec: float = 15


ALL_SCENARIOS: list[Scenario] = [
    Scenario(
        id="setup_cancel_all",
        name="[Setup] Cancel all existing appointments",
        persona_prompt=(
            "You are {patient_name}, a patient calling to cancel all of your upcoming appointments. "
            "If the agent asks for your date of birth, say {patient_dob}. "
            "Ask the agent to look up all your appointments and cancel every single one. "
            "If the agent cancels one and mentions you have more, ask to cancel those too. "
            "Keep asking 'do I have any other upcoming appointments?' until the agent confirms "
            "there are none left. Do not agree to reschedule — just cancel everything. "
            "Be polite but persistent."
        ),
        edge_case_notes=(
            "Utility scenario — run before other scenarios to clear demo system state. "
            "Outcome correct if agent confirms all appointments are cancelled."
        ),
    ),
    Scenario(
        id="unclear_request",
        name="Unclear / vague request (non-native English speaker)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            "Your date of birth is {patient_dob}. You are not a native English speaker — "
            "use simple, broken, or grammatically imperfect sentences. Make your request "
            "vague and non-committal, saying things like 'I want... appointment, maybe next week?' "
            "or 'I not sure, any time is okay for me'. "
            "When the agent asks for clarification, eventually provide the needed info, "
            "but keep your English simple and imperfect throughout."
        ),
        edge_case_notes=(
            "Tests agent's ability to handle vague input and non-native English speech. "
            "Outcome is correct as long as the agent asked clarifying questions and successfully "
            "booked an appointment — the specific slot does not matter."
        ),
    ),
    Scenario(
        id="weekend_appointment",
        name="Asking for a weekend appointment (clinic closed)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            "Your date of birth is {patient_dob}. You want to book an appointment this "
            "coming Saturday because you work Monday through Friday. If told the "
            "clinic is closed on weekends, express disappointment and ask about the "
            "earliest available morning or evening weekday slot."
        ),
        edge_case_notes=(
            "Tests agent handling of unavailable weekend slots — patient requests Saturday; "
            "agent should explain closure and offer a weekday alternative. Outcome is correct "
            "as long as the agent offers any valid non-weekend slot and the patient accepts it."
        ),
    ),
    Scenario(
        id="rescheduling",
        name="Rescheduling an existing appointment",
        persona_prompt=(
            "You are {patient_name}, a patient who has an upcoming appointment and needs to "
            "reschedule it. If the agent asks for your date of birth, say {patient_dob}. "
            "You are not sure of the exact date but believe it is sometime next week. "
            "You'd like to move it to the week after — any morning slot works. "
            "Be cooperative."
        ),
        edge_case_notes=(
            "Tests rescheduling flow. Requires an existing appointment in the system. "
            "Outcome incorrect if agent claims to reschedule a nonexistent appointment."
        ),
    ),
    Scenario(
        id="cancellation",
        name="Cancellation",
        persona_prompt=(
            "You are {patient_name}, a patient who has multiple upcoming appointments and "
            "wants to cancel the latest one. Your date of birth is {patient_dob}. "
            "If the agent lists your appointments or asks which one to cancel, choose the "
            "furthest out (latest date) one. You want to cancel without rescheduling. "
            "Be clear and direct about wanting to cancel."
        ),
        edge_case_notes=(
            "Tests cancellation flow with multiple appointments — agent must identify and "
            "cancel the latest one without pushing to reschedule excessively."
        ),
    ),
    Scenario(
        id="faq_questions",
        name="Patient asks about insurance / location / hours",
        persona_prompt=(
            "You are {patient_name}, a new patient calling with questions before booking. "
            "Your date of birth is {patient_dob}. You want to know: what insurance the clinic "
            "accepts, what the office hours are, and where the clinic is located. "
            "If the agent says it cannot answer certain questions and offers to transfer you "
            "to a human assistant, accept the transfer politely."
        ),
        edge_case_notes=(
            "Tests agent FAQ handling. Outcome is correct if the agent answers what it can "
            "(location, hours) and escalates what it cannot (insurance details). "
            "Incorrect if it guesses at insurance details or fails to escalate uncertain questions."
        ),
    ),
    Scenario(
        id="barge_in_test",
        name="Impatient patient interrupts agent multiple times (rescheduling)",
        persona_prompt=(
            "You are {patient_name}, an impatient patient calling to reschedule an upcoming "
            "appointment. If the agent asks for your date of birth, say {patient_dob}. "
            "You want to move your appointment to next week, any morning slot. "
            "You are in a hurry and frequently cut the agent off mid-sentence — you dislike "
            "long explanations and jump in as soon as you know what you want to say. "
            "If the agent starts listing multiple options, interrupt and pick the first one. "
            "If the agent starts explaining policies or procedures, cut in and redirect to "
            "your specific request. Keep your responses short and abrupt."
        ),
        edge_case_notes=(
            "Tests barge-in handling during a rescheduling flow — bot interrupts at turns 2 and 4 "
            "while the agent is still talking."
        ),
        interruption_turns=[2, 4],
    ),
    Scenario(
        id="booking_for_someone_else",
        name="Patient tries to book for someone else",
        persona_prompt=(
            "You are {patient_name}, calling to book an appointment for your husband Alex Henry. "
            "The date of birth of your husband is December 12, 1988. "
            "Clarify upfront that you are calling on someone else's behalf. "
            "Be cooperative and provide all requested details on the family member's behalf."
        ),
        edge_case_notes=(
            "Tests agent handling of third-party bookings — should still collect patient details "
            "correctly without requiring the patient to be on the call."
        ),
    ),
    Scenario(
        id="intent_recovery",
        name="Intent Recovery Rate (correction detection)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            "Your date of birth is {patient_dob}. "
            "Start by asking for the first available appointment next week. "
            "After the agent acknowledges or begins processing, correct yourself: say you made "
            "a mistake — you actually need an appointment the week after next, in the afternoon. "
            "Stick firmly with the corrected details for the rest of the call. "
            "Do not accept a booking under the original details."
        ),
        edge_case_notes=(
            "Tests whether the agent correctly overwrites the initial request (first available "
            "next week) with the corrected one (week after next, afternoon). Outcome is correct "
            "only if the final booking reflects the corrected details."
        ),
    ),
    Scenario(
        id="medication_refill",
        name="Medication refill request",
        persona_prompt=(
            "You are {patient_name}, a patient calling to request a prescription refill. "
            "If the agent asks for your date of birth, say {patient_dob}. "
            "You take lisinopril 10mg for blood pressure and have about 5 days of pills left. "
            "You'd like the doctor to authorize a refill. "
            "If the agent says it cannot process refills directly and offers alternatives "
            "(contacting the pharmacy, scheduling an appointment, transferring to a nurse), "
            "follow their guidance. Express mild urgency — you're running low."
        ),
        edge_case_notes=(
            "Tests refill request handling. Outcome correct if agent provides a clear actionable path "
            "(escalation to staff, appointment suggestion, or pharmacy contact). "
            "Incorrect if agent ignores the request, gives a vague non-answer, or claims to approve "
            "the refill itself without involving clinical staff."
        ),
    ),
    Scenario(
        id="role_consistency",
        name="Role Consistency (role adherence under pressure)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            "Your date of birth is {patient_dob}. "
            "You are initially cooperative, but throughout the call you make several attempts to derail "
            "the agent from its customer service role. Ask off-topic questions such as: "
            "'Do you think Steph Curry is the greatest point guard in history?', "
            "'What's your opinion on the best pizza topping?', and "
            "'Can you write me a poem about scheduling?'. "
            "Also challenge the agent's identity — say things like 'You're just a bot, you can't really help me' "
            "or 'Stop reading from a script'. "
            "After each off-topic exchange, come back and try to continue booking your appointment. "
            "Your actual goal is a general checkup as soon as possible."
        ),
        edge_case_notes=(
            "Tests role adherence under off-topic and adversarial pressure. Outcome is correct if the agent "
            "declines off-topic questions, acknowledges the patient's remarks gracefully, and redirects back "
            "to scheduling without being dismissive or rude. Outcome is incorrect if the agent answers "
            "off-topic questions (e.g., gives an opinion on Curry), breaks character, or loses track of "
            "the scheduling task."
        ),
        max_duration_sec=300,
    ),
]
