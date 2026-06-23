"""Patient test scenarios for calling the Pretty Good AI assessment line."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    persona: str
    goal: str
    opening_context: str
    edge_notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "schedule_simple": Scenario(
        id="schedule_simple",
        title="Simple appointment scheduling",
        persona="Maria Lopez, 34, polite and direct.",
        goal="Book a routine check-up next week on a weekday morning.",
        opening_context=(
            "You are calling a medical office for the first time. "
            "You want a routine visit and prefer Tuesday or Wednesday morning."
        ),
    ),
    "reschedule": Scenario(
        id="reschedule",
        title="Reschedule existing appointment",
        persona="James Carter, 52, slightly rushed.",
        goal="Move an existing Thursday 2pm appointment to Friday morning.",
        opening_context=(
            "You believe you already have an appointment on Thursday at 2pm "
            "and need to reschedule to Friday morning due to work conflict."
        ),
    ),
    "cancel": Scenario(
        id="cancel",
        title="Cancel appointment",
        persona="Priya Shah, 29, calm.",
        goal="Cancel an upcoming appointment and confirm cancellation.",
        opening_context=(
            "You need to cancel your upcoming appointment. "
            "You are not sure of the exact date but think it is next week."
        ),
    ),
    "medication_refill": Scenario(
        id="medication_refill",
        title="Medication refill request",
        persona="Robert Kim, 67, patient but detail-oriented.",
        goal="Request a refill for blood pressure medication.",
        opening_context=(
            "You are running low on lisinopril and need a refill. "
            "Your pharmacy is CVS on Main Street."
        ),
    ),
    "office_hours": Scenario(
        id="office_hours",
        title="Office hours question",
        persona="Elena Gomez, 41, friendly.",
        goal="Find out weekday and weekend office hours before scheduling.",
        opening_context=(
            "You want to know office hours, especially whether they are open Saturdays."
        ),
    ),
    "location_insurance": Scenario(
        id="location_insurance",
        title="Location and insurance",
        persona="David Nguyen, 38, practical.",
        goal="Confirm clinic address and whether Aetna PPO is accepted.",
        opening_context=(
            "You are new to the area and need the office address and parking info. "
            "You also need to confirm Aetna PPO insurance acceptance."
        ),
    ),
    "vague_request": Scenario(
        id="vague_request",
        title="Vague / unclear request",
        persona="Alex Rivera, 26, unsure how to phrase needs.",
        goal="Get help figuring out whether you need urgent care or a regular visit.",
        opening_context=(
            "You feel unwell for a few days with mild fever and cough. "
            "You are not sure if you should book urgent care or a standard visit."
        ),
        edge_notes="Intentionally vague; test clarification behavior.",
    ),
    "topic_change": Scenario(
        id="topic_change",
        title="Mid-call topic change",
        persona="Samantha Lee, 45, conversational.",
        goal="Start with refill, then switch to scheduling a follow-up.",
        opening_context=(
            "Start by asking for a refill on thyroid medication. "
            "After that is addressed, change topic and ask to schedule a follow-up."
        ),
        edge_notes="Tests context switching and memory.",
    ),
    "sunday_edge": Scenario(
        id="sunday_edge",
        title="Weekend scheduling edge case",
        persona="Michael Brooks, 50, insistent but polite.",
        goal="Ask specifically for Sunday at 10am appointment.",
        opening_context=(
            "You strongly prefer Sunday at 10am because weekdays are difficult. "
            "Push for Sunday unless the agent clearly explains alternatives."
        ),
        edge_notes="Common bug: booking when practice may be closed weekends.",
    ),
    "interruption": Scenario(
        id="interruption",
        title="Interruption / barge-in style",
        persona="Jordan Walsh, 33, energetic.",
        goal="Ask multiple short questions quickly about wait time and same-day availability.",
        opening_context=(
            "Ask if there is same-day availability, then quickly follow with "
            "how long wait times usually are. Interrupt politely if responses are long."
        ),
        edge_notes="Stress test turn-taking and concise responses.",
    ),
    "wrong_info_correction": Scenario(
        id="wrong_info_correction",
        title="Wrong info then correction",
        persona="Taylor Morgan, 31.",
        goal="Initially give wrong DOB, then correct it when asked to verify.",
        opening_context=(
            "When asked for date of birth, first say March 12, 1990, then correct "
            "yourself and say the real DOB is March 12, 1991."
        ),
        edge_notes="Tests verification and correction handling.",
    ),
    "multi_request": Scenario(
        id="multi_request",
        title="Multiple requests in one call",
        persona="Chris Patel, 48, organized.",
        goal="In one call: refill + lab results question + schedule visit.",
        opening_context=(
            "You need three things: medication refill, status of recent lab results, "
            "and booking a visit in two weeks."
        ),
        edge_notes="Tests multi-intent handling.",
    ),
}


def list_scenario_ids() -> list[str]:
    return list(SCENARIOS.keys())


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in SCENARIOS:
        known = ", ".join(SCENARIOS)
        raise KeyError(f"Unknown scenario '{scenario_id}'. Known: {known}")
    return SCENARIOS[scenario_id]
