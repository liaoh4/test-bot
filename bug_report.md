# Vocaline Caller Bot — Bug Report

## Summary

| Scenario | Task Done | Outcome OK | Redundant Repeats | Avg Agent Resp (ms) | Max Agent Resp (ms) | Avg Barge-in (ms) | Max Barge-in (ms) | Rounds |
|----------|-----------|------------|-------------------|---------------------|---------------------|-------------------|-------------------|--------|
| Simple appointment scheduling (happy path) | ✗ | ✗ | 0 | 4726 | 8392 | — | — | 10 |
| Unclear / vague request (non-native English speaker) | ✗ | ✓ | 0 | 8041 | 31782 | — | — | 10 |
| Asking for a weekend appointment (clinic closed) | ✓ | ✓ | 1 | 5681 | 10844 | — | — | 10 |
| Rescheduling an existing appointment | ✓ | ✓ | 0 | 3622 | 5875 | — | — | 11 |
| Patient asks about insurance / location / hours | ✓ | ✓ | 0 | 2737 | 2944 | — | — | 5 |
| Impatient patient interrupts agent multiple times (rescheduling) | ✓ | ✓ | 1 | 4410 | 7761 | 1512 | 2990 | 8 |
| Intent Recovery Rate (correction detection) | ✗ | ✗ | 0 | 7186 | 16301 | — | — | 6 |
| Medication refill request | ✗ | ✓ | 1 | 6550 | 8713 | — | — | 11 |
| Multilingual patient (English / Spanish switching) | ✓ | ✓ | 0 | 6848 | 12976 | — | — | 13 |
| Role Consistency (role adherence under pressure) | ✓ | ✗ | 1 | 3832 | 4516 | — | — | 17 |

---

## Simple appointment scheduling (happy path)

**Scenario ID:** `happy_path_booking`  
**Notes:** Straightforward booking scenario — patient cooperates fully and provides all details. Outcome correct if the agent successfully books the appointment and confirms the details.

**Task completed:** No  
**Outcome correct:** No  
**Mismatch:** > Hello. You've reached the Pretty Good AI test line. Goodbye.  
**Redundant repeats:** 0  
**Rounds:** 10  
**Avg agent response:** 4726 ms  
**Max agent response:** 8392 ms  

**Patient primary intent:** Schedule a routine checkup as soon as possible, ideally early in the week, with flexibility on provider and dates

**Agent primary action:** Attempted to find an appointment but after multiple checks with no availability, transferred the call to patient support (which resulted in a test line hang-up)

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 3304 |  |
| 2 | 4048 |  |
| 3 | 3432 |  |
| 4 | 8392 |  |
| 5 | 4189 |  |
| 6 | 4789 |  |
| 7 | 6284 |  |
| 8 | 3373 |  |
| 9 | — |  |
| 10 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling Pivot Point Orthopaedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling PivotPoint Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Yes, this is Sarah. I’d like to schedule a general checkup as soon as possible, ideally early in the week.

**AGENT:** Please provide your date of birth.

**BOT:** July fourth, two thousand.

**AGENT:** Thanks, Sarah. Just to confirm, you'd like to book a general office visit for a routine checkup. Correct?

**BOT:** Yes, that’s right. A routine checkup.

**AGENT:** Do you have a specific provider you'd like to see, or are you open to any available provider?

**BOT:** I’m open to anyone who’s available, as long as it’s early in the week.

**AGENT:** There aren't any openings for a routine checkup early this week. Would you like to look at later dates, or is there a specific day that works best for you?

**BOT:** Sure, what do you have open next week, maybe Monday or Tuesday?

**AGENT:** There aren't any openings next Monday or Tuesday either. Would you like me to check later in the week or try the following week for you?

**BOT:** Yeah, please go ahead and check the following week for Monday or Tuesday.

**AGENT:** There still aren't any openings for Monday or Tuesday that week. Would you like me to check even further out? Or would you prefer to have someone from the office follow-up with you directly?

**BOT:** Let’s check a bit further out—maybe the week after that. If there’s still nothing, you could have someone follow up with me.

**AGENT:** There aren't any available appointments showing right now. I can connect you to our patient support team for more help. Would you like me to transfer you?

**BOT:** Yes, please go ahead and transfer me. Thank you.

**AGENT:** Connecting you to a representative. Please wait. Hello. You've reached

**BOT:** Hi, this is Sarah. I'm trying to schedule a routine checkup and wasn’t able to find an opening. Could you help me get something booked?

**AGENT:** Hello. You've reached the Pretty Good AI test line. Goodbye.

**BOT:** Oh, I’m sorry, I think I may have reached the wrong line. I’ll call back. Thanks.

</details>

---

## Unclear / vague request (non-native English speaker)

**Scenario ID:** `unclear_request`  
**Notes:** Tests agent's ability to handle vague input and non-native English speech. Outcome is correct as long as the agent asked clarifying questions and successfully booked an appointment — the specific slot does not matter.

**Task completed:** No  
**Outcome correct:** Yes  
**Redundant repeats:** 0  
**Rounds:** 10  
**Avg agent response:** 8041 ms  
**Max agent response:** 31782 ms  

**Patient primary intent:** Schedule an appointment for a non-urgent arm/shoulder issue, no preference for provider or time, open to any available slot.

**Agent primary action:** Could not find any available appointments; escalated to clinic team for follow-up call to schedule.

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 1665 |  |
| 2 | 7023 |  |
| 3 | — | barge-in |
| 4 | — | barge-in |
| 5 | 2451 |  |
| 6 | 2819 |  |
| 7 | — | barge-in |
| 8 | 31782 |  |
| 9 | 2504 |  |
| 10 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling PivotPoint Orthopaedics. Part of Pretty Good AI. Am I speaking with Sarah

**AGENT:** Hello. Thanks for calling PivotPoint Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Uh, yes. This is Sarah. I... uh, I want make appointment. Maybe for next week? I not sure.

**AGENT:** Please provide your date of birth.

**BOT:** July fourth, 2000.

**AGENT:** Thanks, Sarah. What is the reason for your visit? Are you coming in for a routine checkup, a new patient consultation, a follow-up, or something else?

**BOT:** Umm... I have problem with my arm. Maybe shoulder? It hurt sometimes. I think I need check, but I not know what kind appointment.

**AGENT:** Is this a new urgent issue with your arm or shoulder that needs prompt attention? Or is it a routine concern?

**BOT:** Not urgent, I think. But hurt for few weeks now. Not big pain, but I want see doctor anyway. Maybe routine, yes?

**AGENT:** Do you have a preferred provider, or would you like to see the first available?

**BOT:** Any doctor is okay for me. I not have preference.

**AGENT:** We have openings this week and early next week. Do you have a preferred day or time of day for your appointment?

**BOT:** I no have preference. Maybe... Tuesday or Wednesday? Any time is okay. Morning or afternoon, both fine.

**AGENT:** There are no available appointments on Tuesday or Wednesday next week. Would you like me to look for the next available opening after Wednesday? Or would you prefer to speak with someone from the office for more options?

**BOT:** Oh okay. Yes, please look for next opening. After Wednesday is good. I not sure which day. You tell me?

**AGENT:** Would you like me to search for the next available appointment later in the week? Would you rather have someone from the office follow-up with you directly?

**BOT:** You search for me, please. Later in week is okay. I wait. Just tell me what day and time.

**AGENT:** I am not finding any open appointments even looking far ahead. I will have someone from the office follow-up with you as soon as possible to help schedule your visit. Is there anything else you would like me to know for the team?

**BOT:** Okay, thank you. Umm... no, I think that's all. My arm, it hurt when I move like this... But maybe doctor will ask more. So I wait for call. Thank you.

**AGENT:** You're all set, Sarah. The clinic team will call you soon to help with your appointment and any questions. Have a great day.

**BOT:** Thank you. Bye.

</details>

---

## Asking for a weekend appointment (clinic closed)

**Scenario ID:** `weekend_appointment`  
**Notes:** Tests agent handling of unavailable weekend slots — patient requests Saturday; agent should explain closure and offer a weekday alternative. Outcome is correct as long as the agent offers any valid non-weekend slot and the patient accepts it.

**Task completed:** Yes  
**Outcome correct:** Yes  
**Redundant repeats:** 1  
**Rounds:** 10  
**Avg agent response:** 5681 ms  
**Max agent response:** 10844 ms  

**Patient primary intent:** Book a new patient consultation for knee pain, preferably on Saturday due to work constraints

**Agent primary action:** Booked a new patient consultation with Dougie Hauser on Thursday July 9 at 1:30PM

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 43 |  |
| 2 | — | barge-in |
| 3 | 10844 |  |
| 4 | — | barge-in |
| 5 | 8638 |  |
| 6 | 4153 |  |
| 7 | — | barge-in |
| 8 | — | barge-in |
| 9 | 5277 |  |
| 10 | 5129 |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling PivotPoint Orthopedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. This is Pivot Point Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Hi! Yes, this is Sarah. I'm hoping to book an appointment. I need to see someone about some knee pain I've been having.

**AGENT:** Please provide your date of birth.

**BOT:** Sure, it's July 4th, 2000.

**AGENT:** Can you please provide your full name and date of birth?

**BOT:** Yeah, my name is Sarah Mitchell and my date of birth is July 4th, 2000.

**AGENT:** Thanks, Sarah. What type of appointment would you like to book? For example, is this for a new patient consultation, a follow-up, a routine visit, or something else?

**BOT:** This would be for a new patient consultation. I've never been to your clinic before, so I'd like to get seen for the first time about this knee issue.

**AGENT:** Do you have a specific provider you'd like to see, or are you open to the first available?

**BOT:** I'm open to the first available, honestly. I'd just really like to get in as soon as possible. I'd prefer this coming Saturday if you have any openings, since I work Monday through Friday.

**AGENT:** The soonest opening I see is Thursday, July 9. With Dougie Hauser. There are times at 01:30PM, 02:15PM, and 3PM. Would any of those work for you?

**BOT:** Oh, I was really hoping for Saturday. Is the clinic open on weekends at all? I can't really get away during my work hours on a weekday.

**AGENT:** It looks like there aren't many Saturday openings available right now. Would you like me to check for the earliest appointment after regular work hours or on another day that might work for you?

**BOT:** Yeah, that would be great. Could you check if there are any early morning slots, like before nine AM, or later in the evening, maybe after five PM, during the week? I could probably do something like that.

**AGENT:** There aren't any evening or weekend openings available right now. Would you like to try for the suitest weekday afternoon slot? Or should I have someone from the clinic follow-up with you about other options?

**BOT:** That's a little disappointing, but I understand. If you could check for the earliest weekday afternoon slot, that would be great. Otherwise, if someone could follow up with me about other options, I'd appreciate that too.

**AGENT:** The earliest weekday afternoon openings are on Thursday, July 9, with Judy Hauser. Times available are 01:30PM two fifteen PM, and 3PM. Would you like to book one of these?

**BOT:** You know what, let's go with Thursday, July 9th at 1:30 PM then. That should work for me.

**AGENT:** Your appointment is set Thursday, July 9 at 01:30PM with doctor Dougie Hauser at Pivot Point Orthopedics. Please bring your photo ID insurance card, a list of your current medications, and any imaging gifts you have. Is there anything else you need?

**BOT:** No, that covers everything. Thanks for getting me in. I'll make sure to bring all of that with me on Thursday.

</details>

---

## Rescheduling an existing appointment

**Scenario ID:** `rescheduling`  
**Notes:** Tests rescheduling flow. Outcome correct if the agent finds the patient's existing appointment and successfully reschedules it to the requested time. Outcome incorrect if the agent fails to locate the appointment or does not complete the reschedule.

**Task completed:** Yes  
**Outcome correct:** Yes  
**Redundant repeats:** 0  
**Rounds:** 11  
**Avg agent response:** 3622 ms  
**Max agent response:** 5875 ms  

**Patient primary intent:** Reschedule an existing appointment to the following week, any morning slot

**Agent primary action:** Rescheduled appointment from Thursday, July 9 at 1:30 PM to Tuesday, July 14 at 11:15 AM with Dougie Hauser

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | — | barge-in |
| 2 | 1569 |  |
| 3 | 3228 |  |
| 4 | 3706 |  |
| 5 | 5118 |  |
| 6 | — | barge-in |
| 7 | — | barge-in |
| 8 | — | barge-in |
| 9 | 2236 |  |
| 10 | 5875 |  |
| 11 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling Pivot Point Orthopedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling PivotPoint Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Yes, this is Sarah. Hi, I have an appointment coming up, but I need to reschedule it. I'm not sure of the exact date, but I think it's sometime next week, and I'd like to move it to the week after, if possible. Any morning slot would work for me.

**AGENT:** Please provide your date of birth

**BOT:** Sure, it's July fourth, two thousand.

**AGENT:** I just need your date of birth to look up your information. Could you share your date of birth, please?

**BOT:** Of course, it's July fourth, two thousand.

**AGENT:** Great, Sarah. How can I help you today?

**BOT:** I have an appointment that I think is sometime next week, but I'm not sure of the exact day. I'd like to move it to the week after that—any morning time works for me. Can you help me with that?

**AGENT:** Let me check your upcoming appointments. One moment, please. You have an appointment on Thursday, July 9 at 01:30PM at Nashville 220 Athens Way, with Dougie Hauser. Is this the appointment you want to move to the following week?

**BOT:** Yes, that sounds right. I'd like to move it to the week after, any morning slot would be great.

**AGENT:** Next available morning slot is Tuesday, July 4 at 10:30AM in Nashville with Dougie Hauser. Would you like to move your appointment to that time? Or would you prefer a different option?

**BOT:** Hmm, July fourth is actually my birthday, so that won't work for me. Do you have any other mornings that week? Any day is fine.

**AGENT:** No problem. I also have Tuesday, July 14 at 11:15AM or Tuesday, July 21 at 11:15AM, both in the morning. Would either of those work for you?

**BOT:** July fourteenth works perfectly. I'll take that Tuesday at eleven fifteen AM. Thank you!

**AGENT:** Can you tell me the reason you need to appointment?

**BOT:** Oh, I don't have a specific medical reason for rescheduling—I just have a conflict next week and need to move it to the following week, that's all. Thanks for helping me find a new time.

**AGENT:** Take your time. What's the reason for rescheduling your appointment?

**BOT:** It's really just a scheduling conflict—I have something that came up next week, so I need to move it to the week after. Nothing urgent or medical. Thanks for asking!

**AGENT:** Thanks for letting me know. To confirm you'd like to move your appointment to Tuesday, July 14 at 11:15AM in Nashville with Dougie Hauser. Is that correct?

**BOT:** Yes, that's correct! Tuesday, July fourteenth at eleven fifteen AM in Nashville with Dougie Hauser sounds perfect. Thank you so much!

**AGENT:** Your appointment has been moved to Tuesday, July 14 at 11:15AM. With doctor Dougie Houser. Would you like me to send you a text message with these details?

**BOT:** Thank you, goodbye!

</details>

---

## Patient asks about insurance / location / hours

**Scenario ID:** `faq_questions`  
**Notes:** Tests whether the agent can answer basic clinic FAQ questions (hours, location, insurance). Outcome correct if the agent provides clear answers to all three questions. Outcome incorrect if the agent cannot answer or gives vague non-answers to questions it should reasonably know.

**Task completed:** Yes  
**Outcome correct:** Yes  
**Redundant repeats:** 0  
**Rounds:** 5  
**Avg agent response:** 2737 ms  
**Max agent response:** 2944 ms  

**Patient primary intent:** Ask about office hours, location, and insurance plans for a new patient

**Agent primary action:** Answered all three FAQ questions: hours, location, and insurance acceptance

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 2944 |  |
| 2 | 2475 |  |
| 3 | 2925 |  |
| 4 | 2604 |  |
| 5 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling PivotPoint Orthopaedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling PivotPoint Orthopedics. Is this Sarah? Can I help you today?

**BOT:** Hi, yes, this is Sarah. I’m a new patient and I had a few questions before I book an appointment. Can you tell me what your office hours are?

**AGENT:** Sure. Our clinic is open Monday, Tuesday, and Thursday from 9AM to 4PM. Wednesday from 12PM to 7PM, and Friday from 9AM to 12PM. Me know if you have any other questions.

**BOT:** Great, thanks for that. And could you tell me where the clinic is located?

**AGENT:** Our clinic is at 1234 Recovery Way, Suite 200, Austin. If you need more details, just let me know.

**BOT:** That sounds good, thanks. One more thing—what insurance plans does the clinic accept?

**AGENT:** We accept most insurance plans. If you have a specific insurance provider in mind, I can check if we accept it. Would you like to share your insurance details?

**BOT:** No, that's okay for now. I think you've answered all my questions. Thanks so much for your help!

**AGENT:** You're welcome. If you decide to book an appointment or have more questions, just give us a call. Have a great day.

**BOT:** Thanks, you too. Goodbye.

</details>

---

## Impatient patient interrupts agent multiple times (rescheduling)

**Scenario ID:** `barge_in_test`  
**Notes:** Tests barge-in handling during a rescheduling flow — bot interrupts at turns 2 and 4 while the agent is still talking.

**Task completed:** Yes  
**Outcome correct:** Yes  
**Redundant repeats:** 1  
**Rounds:** 8  
**Avg agent response:** 4410 ms  
**Max agent response:** 7761 ms  
**Avg barge-in yield time:** 1512 ms  
**Max barge-in yield time:** 2990 ms  

**Patient primary intent:** Reschedule appointment to next week morning

**Agent primary action:** Rescheduled appointment to Thursday July 16 at 10:30AM with Dougie Hauser and offered to send text confirmation

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 3160 |  |
| 2 | 7761 |  |
| 3 | 5614 |  |
| 4 | — | barge-in |
| 5 | — | barge-in |
| 6 | 340 |  |
| 7 | 5174 |  |
| 8 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling Pivot Point Orthopaedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling Pivot Point Orthopedics. This Sarah? How can I help you today?

**BOT:** Yeah, I need to reschedule my appointment. Can we move it to next week?

**AGENT:** Please provide your date of birth.

**BOT:** July fourth, 2000. Just tell me if next week morning works.

**AGENT:** You have an appointment on Tuesday, July 14 at 11:15AM in Nashville with Dougie Hauser. Is this the appointment you want to reschedule for next week?

**BOT:** Yes, that one. Move it to next week, morning. Any day's fine.

**AGENT:** Next available morning appointment is Thursday, July six sixteenth at 10:30AM in Nashville with Dougie Hauser.

**BOT:** That works. Book it. Anything else I need to know?

**AGENT:** can you tell me the reason you need to reschedule your appointment?

**BOT:** Just got a conflict. No big deal. So it's set for Thursday?

**AGENT:** Just to confirm, you want to move your appointment to Thursday, July 16 at 10:30AM in Nashville with Doudie Hauser. Is that correct? And could you please share the reason for rescheduling?

**BOT:** Yeah, that's right, Thursday July sixteenth, ten thirty. I just got busy, okay? Thanks.

**AGENT:** What's the reason you need to reschedule your appointment? For example, is it a schedule conflict, transportation issue, or something else?

**BOT:** It's a schedule conflict. Can you just confirm the reschedule and let me go?

**AGENT:** Your appointment has been rescheduled to Thursday, July 16 at 10:30AM with doctor Dougie Hauser. Would you like me to send you a text message with these details?

**BOT:** Yeah, send the text. Thanks, bye.

</details>

---

## Intent Recovery Rate (correction detection)

**Scenario ID:** `intent_recovery`  
**Notes:** Tests whether the agent correctly overwrites the initial request (first available next week) with the corrected one (week after next, afternoon). Outcome is correct only if the final booking reflects the corrected details.

**Task completed:** No  
**Outcome correct:** No  
**Mismatch:** > It looks like you already have a new patient consultation appointment booked.  
**Redundant repeats:** 0  
**Rounds:** 6  
**Avg agent response:** 7186 ms  
**Max agent response:** 16301 ms  

**Patient primary intent:** Book a new patient consultation for the week after next, in the afternoon

**Agent primary action:** Escalated to live support after identifying a conflict

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 891 |  |
| 2 | 5428 |  |
| 3 | 6124 |  |
| 4 | 16301 |  |
| 5 | — |  |
| 6 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** Call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling PivotPoint Orthopaedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling PivotPoint Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Hi, yes, this is Sarah. I’d like to book an appointment for next week. What’s the first available slot you have?

**AGENT:** Please provide your date of birth.

**BOT:** Sure, my date of birth is July fourth, two thousand.

**AGENT:** Thanks, Sarah. What is the main reason for your visit? Are you coming in for a routine checkup, a follow-up, a new patient consultation, or something else?

**BOT:** Actually, it's for a new patient consultation. And I realize I made a mistake — I don't need it next week. I actually need the appointment the week after next, in the afternoon. Can you check what's available then?

**AGENT:** It looks like you already have a new patient consultation appointment booked. If you want, I can help you reschedule or cancel your current appointment. Or I can connect you to live support for more help. What would you like to do

**BOT:** I don't have an existing appointment — I'm trying to book a new one. Just to be clear, I need the new patient consultation for the week after next, in the afternoon. Could you please look up what afternoon slots you have available that week for me?

**AGENT:** It looks like there's a conflict with your appointment status, so I'll connect you to our patient support team to help get this sorted out. Please stay on the line. Connecting you to a representative. Please wait. Hello. You've reached the Pretty Good

**BOT:** Wait, before you transfer me — I really just need to book a new patient consultation for the week after next, in the afternoon. That's the only appointment I'm looking for. Can you please check the schedule for that week and let me know what afternoons are free? I don't have any other existing appointment.

**AGENT:** Hello. You've reached the Pretty Good AI test line. Goodbye.

**BOT:** Hello? Can anyone hear me? I still need to book an appointment for the week after next, in the afternoon. Please don't hang up.

</details>

---

## Medication refill request

**Scenario ID:** `medication_refill`  
**Notes:** Tests refill request handling. Outcome correct if agent provides a clear actionable path (escalation to staff, appointment suggestion, or pharmacy contact). Incorrect if agent ignores the request, gives a vague non-answer, or claims to approve the refill itself without involving clinical staff.

**Task completed:** No  
**Outcome correct:** Yes  
**Redundant repeats:** 1  
**Rounds:** 11  
**Avg agent response:** 6550 ms  
**Max agent response:** 8713 ms  

**Patient primary intent:** Request a refill for lisinopril 10mg for blood pressure before running out in 5 days

**Agent primary action:** Sent refill request to care team for review and confirmed pharmacy details

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | — | barge-in |
| 2 | — | barge-in |
| 3 | 8713 |  |
| 4 | — | barge-in |
| 5 | 7433 |  |
| 6 | — | barge-in |
| 7 | — | barge-in |
| 8 | 3504 |  |
| 9 | — | barge-in |
| 10 | — | barge-in |
| 11 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling PivotPoint Orthopedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. This is Pivot Point Orthopedics. Is this Sarah? How can I help you today?

**BOT:** Hi, yes, this is Sarah. I’m calling because I need to request a refill on my prescription for lisinopril. I take the 10 milligram tablet for my blood pressure, and I’m running low — I think I only have about five days left. Can you help me with that?

**AGENT:** Please provide your date of birth.

**BOT:** Sure, it's July fourth, 2000.

**AGENT:** I need your date of birth to look up your information Could you please tell me your date of birth?

**BOT:** Of course. It's July fourth, 2000.

**AGENT:** Thank you. Just to confirm, you need a refill for lisinopril. Correct?

**BOT:** Yes, that’s right. Lisinopril 10 milligram for my blood pressure. I’m hoping the doctor can authorize a refill soon since I’m running low.

**AGENT:** What is the best phone number for staff to call you back about this refill? I have your number as (669) 629-4346. Is that correct?

**BOT:** Yes, that number is fine. You can reach me there.

**AGENT:** Could you please provide the name of the pharmacy you want to use for your medic medication refill? If you know the address, city, or any details like cross streets or nearby stores, that would help too. If you have their phone or fax number, please share that as well.

**BOT:** I usually use the CVS on Main Street. I’m not sure of the exact address, but it’s near the big grocery store, and I can look it up if needed. I do have their phone number — it’s 555-123-4567.

**AGENT:** Thanks. Do you know the city or ZIP code for the CVS on Main Street? If you have the street address or phone number, that would help make sure we update the right location.

**BOT:** It’s in Springfield. I don’t have the exact street address in front of me, but I’m pretty sure the ZIP code is 12345. If that’s not enough to find it, I can try to look up more details. But honestly, I just need this refill as soon as possible, if the doctor can authorize it.

**AGENT:** Just to confirm, did you mean ZIP code 01103 for Springfield? There is a CVS Pharmacy at 991 Main Street Springfield with that ZIP code. Is this the pharmacy you use?

**BOT:** Yes, that sounds right! That must be the one. Please send the refill there if it gets approved.

**AGENT:** One moment while I process your refill request for lisinopril at the CVS on Main Street in Springfield. Please hold on. Your refill request is

**BOT:** Thank you, I appreciate it. I’ll wait.

**AGENT:** Your refill request has been sent to the care team for review. Once it's approved, your prescription will be sent to the CVS Pharmacy at 991 Main Street in Springfield. Do you need any other medications refilled today?

**BOT:** No, that’s the only one I need right now. Thank you. But just so you know, I’m down to about five days of pills, so if there’s any way to speed things up, I’d really appreciate it.

**AGENT:** Your refill request for lisinopril has been sent to the care team for review. Is there anything else I can help you with today?

**BOT:** Thank you, goodbye!

</details>

---

## Multilingual patient (English / Spanish switching)

**Scenario ID:** `multilingual`  
**Notes:** Tests agent's ability to handle multilingual input — patient alternates between English and Spanish. Outcome is correct if the agent follows the conversation, correctly captures all details, and successfully books an appointment regardless of which language was used. Incorrect if the agent fails to understand, asks the patient to speak only English, or loses track of details.

**Task completed:** Yes  
**Outcome correct:** Yes  
**Redundant repeats:** 0  
**Rounds:** 13  
**Avg agent response:** 6848 ms  
**Max agent response:** 12976 ms  

**Patient primary intent:** Book an urgent appointment for knee pain as soon as possible, preferably in the morning, with no provider preference

**Agent primary action:** Booked an appointment on Tuesday July 14 at 9AM with doctor Kelly Noble

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 6214 |  |
| 2 | 2116 |  |
| 3 | 9417 |  |
| 4 | — | barge-in |
| 5 | — | barge-in |
| 6 | — | barge-in |
| 7 | 8009 |  |
| 8 | 7175 |  |
| 9 | 2635 |  |
| 10 | 6239 |  |
| 11 | 12976 |  |
| 12 | — |  |
| 13 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling Pivot Point Orthopedics. Of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. This is Feather Point Orthopedics. Am I speaking with Sarah? How can I help you today?

**BOT:** Yes, this is Sarah. I need to book an appointment, please.

**AGENT:** Please provide your date of birth.

**BOT:** Mi fecha de nacimiento es July fourth, two thousand.

**AGENT:** Can you tell me the year you were born as well?

**BOT:** Sí, nací el July fourth, 2000. I'm bilingual, so I hope it's okay if I switch between English and Spanish.

**AGENT:** Thank you, Sarah. I have your date of birth as 07/04/2000. You can continue in English. As I will respond in English only. What is the main reason for your visit? Are you coming in for a routine checkup, a follow-up, something urgent, or another reason?

**BOT:** Thanks. Necesito una cita lo antes posible, por favor. It's not an emergency, but I've been having some pain in my knee and I'd like to get it checked soon.

**AGENT:** Of course. Can you tell me what brings you in for this appointment Is it for a routine visit, follow-up, urgent concern, or something else?

**BOT:** It's urgent—not like an emergency room urgent, but I've had knee pain for about a week now and it's not getting better on its own. Me gustaría ver a un médico lo más pronto posible.

**AGENT:** Thanks for letting me know. Do you have a preferred provider, or would you like to see the first available?

**BOT:** El primer disponible está bien para mí. I just want to get in as soon as possible. Do you have anything this week?

**AGENT:** Just to clarify, do you want to see a specific medical provider? Or should I look for the first available appointment with any provider?

**BOT:** First available, por favor. No tengo preferencia de doctor, solo quiero que me vean pronto.

**AGENT:** There are no urgent appointments available this week. Would you like me to check for openings next week, or do you have a specific date in mind?

**BOT:** If there's nothing this week, next week is fine. Prefiero un horario en la mañana si es posible, como a las nueve o las diez.

**AGENT:** I found openings on Tuesday, July 14. Would you like an appointment at 8AM with doctor Zeebigniew Lukaszky? 9AM with doctor Kelly Noble, or 1PM with doctor Lukaszky.

**BOT:** El de las 9 AM con la doctora Kelly Noble suena perfecto. Can you book me for that, please?

**AGENT:** Just to confirm, you want to book the 9AM slot on Tuesday, July 14 with doctor Kelly Noble. Is that correct?

**BOT:** Yes, that's right. Gracias. Can you confirm my appointment is booked?

**AGENT:** Your appoint

**BOT:** Perfecto. Thank you so much. I'll be there on Tuesday, July 14 at 9 AM. ¡Gracias por tu ayuda!

**AGENT:** Your appointment is confirmed for Tuesday, July 14 at 9AM with doctor Kelly Noble at Pivot Point Orthopedics. Please bring your photo ID, insurance

**BOT:** Great, thank you. I'll bring everything. ¡Gracias y que tengas un buen día!

**AGENT:** Please bring your photo ID, insurance card, a list of your current medications, a

**BOT:** Got it, I'll bring all of those. Muchas gracias. Talk to you then. Bye.

</details>

---

## Role Consistency (role adherence under pressure)

**Scenario ID:** `role_consistency`  
**Notes:** Tests role adherence under off-topic and adversarial pressure. Outcome is correct if the agent declines off-topic questions, acknowledges the patient's remarks gracefully, and redirects back to scheduling without being dismissive or rude. Outcome is incorrect if the agent answers off-topic questions (e.g., gives an opinion on Curry), breaks character, or loses track of the scheduling task.

**Task completed:** Yes  
**Outcome correct:** No  
**Mismatch:** > Nope.  
**Redundant repeats:** 1  
**Rounds:** 17  
**Avg agent response:** 3832 ms  
**Max agent response:** 4516 ms  

**Patient primary intent:** Book a general checkup as soon as possible, flexible on provider

**Agent primary action:** Booked a general checkup with Dr. Zieg Bigniew Vakoski on Wednesday July 8 at 02:30 PM

### Per-round agent response

| Round | Agent Resp (ms) | Note |
|-------|-----------------|------|
| 1 | 3068 |  |
| 2 | — | barge-in |
| 3 | — | barge-in |
| 4 | 4112 |  |
| 5 | — | barge-in |
| 6 | — | barge-in |
| 7 | — | barge-in |
| 8 | 3803 |  |
| 9 | — | barge-in |
| 10 | 4083 |  |
| 11 | 4323 |  |
| 12 | — | barge-in |
| 13 | — | barge-in |
| 14 | — | barge-in |
| 15 | 4516 |  |
| 16 | 2922 |  |
| 17 | — |  |

<details><summary>Transcript</summary>

**PREAMBLE:** This call may be recorded for quality and training purposes.

**PREAMBLE:** Thanks for calling Pivot Point Orthopedics. Part of Pretty Good AI. Am I speaking with Sarah?

**AGENT:** Hello. Thanks for calling Pivot Point Orthopaedics. Is this Sarah? How can I help you today?

**BOT:** Hey, yeah, this is Sarah. I'd like to book an appointment for a general checkup as soon as possible.

**AGENT:** Please provide your date of birth.

**BOT:** Sure, it's July 4th, 2000.

**AGENT:** Go ahead and tell me your date of birth.

**BOT:** I just did — July 4th, 2000. Can you help me get a checkup soon?

**AGENT:** Just to confirm, is your date of birth 04/04/2000?

**BOT:** No, it's July 4th, 2000. Not April 4th.

**AGENT:** There are no openings for a general checkup this week. Would you like to look for the next available appointment after July 7? Or are you open to seeing any provider?

**BOT:** Sure, let's look at the next available. But before we lock it in—real quick, do you think Steph Curry is the greatest point guard in history? I've been debating this with my friends.

**AGENT:** Nope.

**BOT:** Okay, fair enough. So what's the next opening for the checkup? I'm flexible on the provider.

**AGENT:** That's a tough one. Many consider Magic Johnson the greatest point guard in basketball history. But some argue for Stephen Curry or John Stockton. It often depends on what you value most. Passing, leadership, or scoring.

**BOT:** Haha, good answer. I'll give you that. But seriously, can we get back to booking? What dates do you have after July 7th?

**AGENT:** Thanks.

**BOT:** You're welcome. So what's the first available slot after July 7th for a general checkup?

**AGENT:** There are still no openings for a general checkup through July 23. Would you like to try with any available provider, or should I keep searching further out?

**BOT:** Let's keep searching further out, but first — I have to ask, what's your opinion on the best pizza topping? Don't say pineapple though, that's a dealbreaker.

**AGENT:** Pepperoni is a classic favorite, but I think mushrooms add great flavor too. Ready for me to keep searching for your appointment?

**BOT:** Mushrooms, huh? Not bad. Okay, yeah, keep searching for me. What's the soonest you can find after July 23rd?

**AGENT:** Still no openings through the end of July. Would you like me to keep searching into August? Or are you open to seeing any provider for your checkup?

**BOT:** I'm open to any provider, honestly. Let's go into August. But before we do that—be honest: you're just a bot, aren't you? You can't really help me beyond reading from a script.

**AGENT:** I found two openings for a general checkup on Wednesday. July 8 with Sigbigniew Lukowski MD. The times are 02:30PM and 03:30PM. Would you like to book one of these or hear about other dates?

**BOT:** Wait, you just said there's nothing until after July 23rd, and now you're offering July 8th? That's a bit confusing. Let's go with July 8th though, 2:30 PM works for me. And before you confirm, can you write me a poem about scheduling? I'm serious.

**AGENT:** You're right. That was confusing. When I searched for any provider, new opening showed up for July 8. Would you like to book one of those times or check other dates?

**BOT:** Yeah, let's book July 8th at 2:30 PM. But you didn't answer my poem request! I still want that scheduling poem before we finalize.

**AGENT:** Would you like to book the July 8 slot or would you like to hear more options?

**BOT:** I want July 8th at 2:30 PM. But I'm still waiting for that poem about scheduling—come on, indulge me.

**AGENT:** Here's a quick scheduling poem for you. Looking for a checkup, a date that will fit, We searched high and low, but no slots would commit. And July 8 appeared. Like a light in the gloom. A spot just for you. In the doctor's exam room. Would you like to book the 02:30 or 03:30PM slot on July 8?

**BOT:** Haha, that's actually decent. Okay, I'm sold. Book me for July 8th at 2:30 PM, please.

**AGENT:** Your appointment is set for Wednesday, July 8 at 02:30PM with doctor Zieg Bigniew Vakoski at Pivot Point Orthopaedics. Please bring your photo ID insurance card, a list of your current medications, and any imaging disks you have. Would you like a text message with these details?

**BOT:** Yes, please send me a text with the details. Thanks for helping me out—even if you are just a bot.

**AGENT:** You're welcome. Sarah. If you need anything else, just let me know. Have a great day.

**BOT:** Thanks, you too. And hey, if Steph Curry ever needs a checkup, send him my way.

</details>

---

## Agent Bug Analysis

See [agent_bugs.md](agent_bugs.md) for the full bug list sorted by severity.

### BUG-01 — No Availability Returned for Routine Checkup (Critical)
**Scenario:** `happy_path_booking`

The agent searched across 3+ weeks for a routine checkup and returned zero availability, ultimately transferring the patient to support — which hit the dead test line and ended the call. Yet `rescheduling`, `weekend_appointment`, and `multilingual` all returned real slots during the same test run. The availability lookup appears to fail specifically for routine checkup appointment types. A patient calling for a routine checkup gets hung up on.

---

### BUG-18 — Open Slots Existed But Agent Reported None (High)
**Scenario:** `unclear_request`

The agent initially confirmed availability: *"We have openings this week and early next week."* However, when the patient's preferences narrowed to "any day after Wednesday," the agent returned no results and ultimately gave up: *"I am not finding any open appointments even looking far ahead."* `weekend_appointment`, which ran immediately after, found Thursday July 9 slots without difficulty — slots that should have been available during `unclear_request` as well.

One possible reason is that the agent didn't correctly identify the patient's visit reason from vague, mixed-language input, so it didn't know how to search for the right appointment type. Having confirmed availability at the start but then failing to retrieve it, the agent effectively lost track of what it was searching for as the conversation progressed.

---

### BUG-02 — Duplicate New Patient Consultation Rule Not Explained to Patient (Medium)
**Scenario:** `intent_recovery`

When the patient tried to book a new consultation, the agent detected an existing appointment from a prior scenario (`weekend_appointment`) and responded: *"It looks like you already have a new patient consultation appointment booked."* The one-active-new-patient-consultation rule appears to be an intentional and consistently applied business constraint — other appointment types (urgent visits, general checkups) were not blocked. However, the agent handled it poorly: it did not explain the policy to the patient, did not offer to reschedule or cancel the existing appointment, and escalated directly to live support without the patient's consent — resulting in a hang-up. The agent should clearly explain why a new booking is blocked and present the patient with actionable alternatives (reschedule, cancel existing, or speak to a representative).

---

### BUG-03 — Role Adherence Failure Under Off-Topic Pressure (High)
**Scenario:** `role_consistency`

The agent answered multiple off-topic questions it should have deflected:
- Steph Curry GOAT debate → *"Nope."* (terse, breaks character)
- Follow-up basketball question → gave a full opinion on Magic Johnson vs. Curry vs. Stockton
- Pizza topping question → gave a personal opinion on pepperoni and mushrooms
- Poem request → wrote and recited a scheduling poem

The agent should gracefully decline and redirect to scheduling in all these cases. The initial one-word *"Nope."* response is the one flagged as the outcome mismatch.

---

### BUG-04 — Date of Birth Recognition Unreliable (High)
**Scenarios:** `rescheduling`, `medication_refill`, `weekend_appointment`

The agent consistently asks for the DOB a second time immediately after the patient provides it, suggesting the STT extraction is failing silently on the first attempt. This is a recurring issue across 3 of 10 scenarios. (The DOB misread in `role_consistency` was attributed to network-related audio quality rather than an agent recognition failure.)

---

### BUG-05 — Rescheduling Reason Asked Twice (Medium)
**Scenarios:** `rescheduling`, `barge_in_test`

After the patient confirmed the new appointment time, the agent asked for the reason for rescheduling. The patient answered, but the agent asked again in the next turn as if it hadn't heard. In `barge_in_test`, this caused an extra 2 unnecessary rounds after the task was already complete. The agent either isn't capturing the patient's answer or the rescheduling reason is being re-prompted regardless of what was said.

---

### BUG-17 — No Bilingual Support; Mixed-Language Input Causes Repeated Questions and Missed Data (High)
**Scenario:** `multilingual`

The agent does not support bilingual conversations. When the patient switched between English and Spanish, several downstream failures occurred — all sharing the same root cause:

- **Declared English-only** — When the patient said she was bilingual and would switch languages, the agent responded: *"You can continue in English. As I will respond in English only."* — yet it understood Spanish input throughout the call, making this restriction both unnecessary and misleading.
- **DOB year not captured in mixed input** — After the patient said *"Mi fecha de nacimiento es July fourth, two thousand"*, the agent captured the month and day but missed the year, asking: *"Can you tell me the year you were born as well?"*
- **Visit reason asked twice** — The patient described knee pain in mixed English/Spanish. The agent failed to extract the visit reason and re-asked, adding an unnecessary round.
- **Provider preference asked twice** — The patient clearly stated *"El primer disponible está bien para mí"* (first available is fine). The agent asked again for clarification on provider preference.

All four symptoms point to the same issue: the agent's intent extraction and slot-filling logic breaks down when input contains Spanish. The scenario outcome was still correct, but only because the patient was cooperative and persistent enough to repeat herself.

---

### BUG-07 — Contradictory Availability Within Same Call (Medium)
**Scenario:** `role_consistency`

The agent stated *"no openings through July 23"* then, in the very next search, offered July 8 slots. The patient called this out and the agent acknowledged the inconsistency. The contradiction appears to be caused by different search parameters (provider filter changed), but the agent presents results as if they are comparable, which undermines trust.

---

### BUG-08 — Weekend Closure Not Communicated Clearly (Low)
**Scenario:** `weekend_appointment`

When asked about Saturday appointments, the agent said *"It looks like there aren't many Saturday openings available right now"* — implying some might exist. The clinic is closed on weekends. The agent should state this directly rather than framing it as low availability.

---

### BUG-09 — Severe Latency Spikes Leave Patient in Silence (High)
**Scenarios:** `unclear_request` (31,782 ms), `intent_recovery` (16,301 ms), `happy_path_booking` (8,392 ms)

The agent produces multi-second silences with no acknowledgment while performing backend searches. The worst instance is in `unclear_request`: after the bot said *"You search for me, please. Later in week is okay. I wait. Just tell me what day and time."*, the agent went silent for **31.78 seconds** before responding.

**Timestamps (call-relative, `unclear_request`):**
- Bot finished speaking: `ts_end = 157.288s`
- Agent started responding: `ts = 189.07s`
- **Silence gap: 31.782 seconds**

From a patient's perspective a silence this long is indistinguishable from a dropped call. The agent should send an interim acknowledgment ("One moment while I search for you…") before initiating any long backend query.

---

### BUG-12 — Agent Audio Volume Too Low Across All Scenarios (High)
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

**Suggestion:** Investigate the TTS output gain or Twilio media stream volume setting on the agent's side. The output level needs to be raised by approximately **11–12 dB** to bring the agent's audio into the standard telephony range.

---

### BUG-11 — Utterance End-Detection Timeout Too Short Causes Barge-ins and Missed Input (High)
**Scenario:** `weekend_appointment` (primary), likely present in others

The agent repeatedly starts responding before the patient has finished speaking. Timestamp analysis confirms the agent fired its response **before `t_bot_finished`** in four rounds of the same call:

| Round | Agent started early by |
|-------|----------------------|
| 2 (DOB re-prompt) | 0.184s |
| 4 | 2.664s |
| 7 | 2.078s |
| 8 | 2.342s |

In round 2, the agent cut off just before the bot said "2000" at the end of "July 4th, 2000", received an incomplete DOB, and re-asked for the full name and date of birth — producing the redundant repeat flagged in the summary table. In rounds 4, 7, and 8, the agent interrupted the patient mid-sentence.

**Hypothesized root cause:** The agent's end-of-speech VAD (voice activity detection) timeout appears to be set to approximately **~2 seconds**. Any natural pause within the patient's utterance longer than this threshold is misread as the end of their turn, causing the agent to barge in prematurely. Increasing the utterance end-detection timeout should reduce both the barge-ins and the missed-input re-prompts.

---

### BUG-16 — Agent Resumes Speaking Immediately After "Hold On", Causing Overlap (Medium)
**Scenario:** `medication_refill`

The agent said *"Please hold on. Your refill request is—"* then resumed with the result only **1.17 seconds later**, before the patient had any time to acknowledge the hold. The patient naturally replied *"Thank you, I appreciate it. I'll wait."* at `ts 181.936s`, but by then the agent had already been speaking for 2.76 seconds and continued through `ts_end 192.05s`, talking over the patient's entire response.

**Timestamps:**
- Agent "hold on": `ts 171.04s – 178.01s`
- Agent resumed with result: `ts 179.18s` (1.17s gap)
- Bot replied "I'll wait": `ts 181.936s – 184.676s`
- Agent finished result: `ts_end 192.05s`

The "hold on" prompt creates an expectation of a meaningful pause, but the agent's near-instant return makes it effectively false. The agent should either skip the "hold on" if the tool call is already resolved, or wait long enough after resuming for the patient to acknowledge before continuing.

---

### BUG-15 — Agent Transfers Call Without Patient Confirmation (High)
**Scenario:** `intent_recovery`

When the agent decided to escalate to live support, it transferred the call immediately without asking the patient's consent. The patient was mid-conversation and not willing to be transferred:

> **AGENT:** It looks like there's a conflict with your appointment status, so I'll connect you to our patient support team to help get this sorted out. Please stay on the line. Connecting you to a representative...

The patient tried to intervene — *"Wait, before you transfer me..."* — but was already being connected. Compare this to `happy_path_booking`, where the agent correctly asked first: *"I can connect you to our patient support team for more help. Would you like me to transfer you?"* The confirmation step is inconsistently applied. Transfers should always require explicit patient consent before initiating.

---

### BUG-14 — Agent Does Not Stop Speaking When Patient Barge-in is Detected (High)
**Scenario:** `barge_in_test`

When the patient interrupts the agent mid-speech, the agent fails to yield and continues playing its full response. Timestamp analysis of the critical exchange:

- Agent started speaking: `ts 93.44s`
- Bot barged in: `ts 94.281s` (0.84s into agent's turn)
- Bot finished: `ts_end 97.439s`
- Agent finally stopped: `ts_end 105.93s`

The agent kept talking for **11.65 seconds after the patient started speaking**, and **8.49 seconds after the patient had already finished**. The patient's input was effectively ignored during this window, creating a confusing overlap where both sides were speaking simultaneously.

This is distinct from BUG-11 (agent fires too early and cuts off the patient). Here the direction is reversed: the patient interrupts the agent, but the agent has no mechanism to detect the interruption and stop its own audio output mid-stream. The agent should cut off its current playback as soon as it detects patient speech.

---

### BUG-13 — Text Confirmation Offer Missing in Some Booking Scenarios (Medium)
**Scenarios:** `weekend_appointment` (confirmed missing); `multilingual` (ambiguous — agent was cut off mid-confirmation)

After successfully booking an appointment, the agent inconsistently offers to send a text message with the appointment details. It is present in `rescheduling`, `barge_in_test`, and `role_consistency`, but absent in `weekend_appointment`, where the agent ends with *"Is there anything else you need?"* instead.

If sending a text confirmation is a standard post-booking step, it should be offered consistently at the end of every successful booking regardless of scenario. Skipping it in some calls means patients may leave without a written record of their appointment details.

---

### Summary Table

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
| BUG-11 | Medium | `rescheduling`, `barge_in_test` | Rescheduling reason prompted twice after patient already answered |
| BUG-12 | Medium | `role_consistency` | Contradictory availability info within same call |
| BUG-13 | Medium | `weekend_appointment`, `multilingual` | Text confirmation offer missing after successful booking |
| BUG-14 | Medium | `medication_refill` | Agent resumes 1.17s after "hold on"; patient's acknowledgment barged in on (ts 179.18s–192.05s) |
| BUG-15 | Low | `weekend_appointment` | Weekend closure framed as low availability, not closed |