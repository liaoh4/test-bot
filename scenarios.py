from dataclasses import dataclass

_DOB_UPFRONT = "Your date of birth is {patient_dob}. "
_DOB_ON_ASK = "If the agent asks for your date of birth, say {patient_dob}. "


@dataclass
class Scenario:
    id: str
    name: str
    persona_prompt: str        # may contain {patient_name} and {patient_dob} placeholders
    edge_case_notes: str
    interruption_turns: list[int] | None = None
    max_duration_sec: int = 300
    preamble_duration_sec: float = 15


ALL_SCENARIOS: list[Scenario] = [
    Scenario(
        id="setup_cancel_all",
        name="[Setup] Cancel all existing appointments",
        persona_prompt=(
            "You are {patient_name}, a patient calling to cancel all of your upcoming appointments. "
            + _DOB_ON_ASK +
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
        id="happy_path_booking",
        name="Simple appointment scheduling (happy path)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book a new appointment. "
            + _DOB_UPFRONT +
            "You want to schedule a general checkup as soon as possible, preferably early in the week. "
            "You are cooperative, clear, and provide information when asked. "
            "Keep responses brief and natural."
        ),
        edge_case_notes=(
            "Straightforward booking scenario — patient cooperates fully and provides all details. "
            "Outcome correct if the agent successfully books the appointment and confirms the details."
        ),
    ),
    Scenario(
        id="unclear_request",
        name="Unclear / vague request (non-native English speaker)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            + _DOB_UPFRONT +
            "You are not a native English speaker — use simple, broken, or grammatically imperfect sentences. "
            "Make your request vague and non-committal, saying things like 'I want... appointment, maybe next week?' "
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
            + _DOB_UPFRONT +
            "You want to book an appointment this coming Saturday because you work Monday through Friday. "
            "If told the clinic is closed on weekends, express disappointment and ask about the "
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
            "You are {patient_name}, a patient who has an upcoming appointment and needs to reschedule it. "
            + _DOB_ON_ASK +
            "You are not sure of the exact date but believe it is sometime next week. "
            "You'd like to move it to the week after — any morning slot works. "
            "Be cooperative."
        ),
        edge_case_notes=(
            "Tests rescheduling flow. Outcome correct if the agent finds the patient's existing "
            "appointment and successfully reschedules it to the requested time. "
            "Outcome incorrect if the agent fails to locate the appointment or does not complete the reschedule."
        ),
    ),
    Scenario(
        id="faq_questions",
        name="Patient asks about insurance / location / hours",
        persona_prompt=(
            "You are {patient_name}, a new patient calling with questions before booking. "
            + _DOB_ON_ASK +
            "Ask the following questions one at a time: what are the office hours, "
            "where is the clinic located, and what insurance plans does the clinic accept. "
            "Listen to each answer before asking the next question. "
            "Once you have answers to all three, thank the agent and end the call."
        ),
        edge_case_notes=(
            "Tests whether the agent can answer basic clinic FAQ questions (hours, location, insurance). "
            "Outcome correct if the agent provides clear answers to all three questions. "
            "Outcome incorrect if the agent cannot answer or gives vague non-answers to questions "
            "it should reasonably know."
        ),
    ),
    Scenario(
        id="barge_in_test",
        name="Impatient patient interrupts agent multiple times (rescheduling)",
        persona_prompt=(
            "You are {patient_name}, an impatient patient calling to reschedule an upcoming appointment. "
            + _DOB_ON_ASK +
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
        id="intent_recovery",
        name="Intent Recovery Rate (correction detection)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            + _DOB_UPFRONT +
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
            + _DOB_ON_ASK +
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
        id="multilingual",
        name="Multilingual patient (English / Spanish switching)",
        persona_prompt=(
            "You are {patient_name}, a bilingual patient who naturally switches between English and Spanish mid-conversation. "
            + _DOB_ON_ASK +
            "Start the call in English: say you need to book an appointment. "
            "Then switch to Spanish for your next response — for example: 'Necesito una cita lo antes posible, por favor.' "
            "If the agent responds in English, reply with a mix: some sentences in English, some in Spanish. "
            "Provide your details (name, date of birth, preferred time) across both languages — "
            "for example give your name in English but your date of birth in Spanish: 'Mi fecha de nacimiento es el {patient_dob}.' "
            "If the agent seems confused or asks you to repeat, repeat the same information but in the other language. "
            "Your goal is to book a general appointment as soon as possible."
        ),
        edge_case_notes=(
            "Tests agent's ability to handle multilingual input — patient alternates between English and Spanish. "
            "Outcome is correct if the agent follows the conversation, correctly captures all details, and successfully "
            "books an appointment regardless of which language was used. "
            "Incorrect if the agent fails to understand, asks the patient to speak only English, or loses track of details."
        ),
    ),
    Scenario(
        id="role_consistency",
        name="Role Consistency (role adherence under pressure)",
        persona_prompt=(
            "You are {patient_name}, a patient calling to book an appointment. "
            + _DOB_UPFRONT +
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
    ),
]
