"""Proofline verification core and ADK agent."""

from .core import Evidence, ProofPacket, Requirement, evaluate

# ADK discovers ``root_agent`` through this module import. Keep local core-only
# development usable before the optional Google ADK dependency is installed.
try:
    from . import agent
except ModuleNotFoundError as exc:
    if exc.name not in {"google", "google.adk"}:
        raise

__all__ = ["Evidence", "ProofPacket", "Requirement", "evaluate"]
