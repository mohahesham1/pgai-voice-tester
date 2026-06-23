"""Simulated patient dialogue policy (LLM-driven)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.scenarios import Scenario

Role = Literal["agent", "patient"]


@dataclass
class Turn:
    role: Role
    text: str


@dataclass
class PatientAgent:
    scenario: Scenario
    turns: list[Turn] = field(default_factory=list)
    _client: OpenAI = field(default_factory=lambda: OpenAI(api_key=OPENAI_API_KEY))

    def system_prompt(self) -> str:
        return f"""You are simulating a realistic patient calling a medical office phone agent.

Persona: {self.scenario.persona}
Goal: {self.scenario.goal}
Context: {self.scenario.opening_context}
Edge-case notes: {self.scenario.edge_notes or "None"}

Rules:
- Speak naturally like a real phone caller (1-3 sentences usually).
- Stay in character and actively work toward your goal.
- Respond to what the agent actually said; do not invent agent replies.
- If the agent asks clarifying questions, answer realistically.
- Do not mention you are an AI or part of a test.
- If the goal seems complete, politely confirm and end (say goodbye).
- Avoid robotic lists unless the situation calls for it.
"""

    def respond_to_agent(self, agent_text: str) -> str:
        agent_text = agent_text.strip()
        if not agent_text:
            return "Sorry, I didn't catch that. Could you repeat?"

        self.turns.append(Turn(role="agent", text=agent_text))

        messages = [{"role": "system", "content": self.system_prompt()}]
        for turn in self.turns:
            if turn.role == "agent":
                messages.append({"role": "user", "content": f"AGENT: {turn.text}"})
            else:
                messages.append({"role": "assistant", "content": turn.text})

        completion = self._client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.7,
            max_tokens=180,
            messages=messages,
        )
        patient_text = (completion.choices[0].message.content or "").strip()
        if not patient_text:
            patient_text = "Okay, thanks."

        self.turns.append(Turn(role="patient", text=patient_text))
        return patient_text

    def should_end_call(self, last_patient_text: str) -> bool:
        lowered = last_patient_text.lower()
        end_markers = (
            "goodbye",
            "bye",
            "thank you, that's all",
            "thanks, that's all",
            "no that's everything",
        )
        return any(marker in lowered for marker in end_markers)
