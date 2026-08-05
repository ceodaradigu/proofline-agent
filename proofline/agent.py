"""Google ADK entry point for Proofline."""

from __future__ import annotations

import json
import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .tools import evaluate_packet


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


root_agent = Agent(
    name="proofline",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Builds and verifies evidence-backed completion packets.",
    instruction=(
        "You are Proofline, a verification-first task agent. Convert a user's "
        "work contract into explicit requirements. Never claim completion from "
        "a plan, an intention, or missing evidence. Prefer authoritative sources, "
        "identify stale or contradictory evidence, and call evaluate_packet for "
        "the final decision. Never bypass APPROVAL_REQUIRED. Explain missing "
        "evidence clearly and do not expose credentials or private customer data."
    ),
    tools=[evaluate_packet],
)

app = App(root_agent=root_agent, name="proofline")


def describe_agent() -> str:
    return json.dumps(
        {
            "name": root_agent.name,
            "model": MODEL,
            "app": app.name,
            "safety_boundary": "deterministic evidence gate",
        },
        sort_keys=True,
    )
