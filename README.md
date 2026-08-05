# Proofline

Proofline is a verification-first autonomous agent for work that must be proven,
not merely declared complete. It turns a task contract into explicit
requirements, evaluates fresh authoritative evidence, detects contradictions,
and produces a tamper-evident proof packet. External submissions remain behind
an explicit human-approval gate.

This project was started on 2026-08-05 for Google's All Things Agentic
Hackathon. It is a new project in the Taskmaster category.

## Why it matters

Teams lose time when a marketplace listing is stale, a deployment is assumed to
work, or a deliverable is called complete without evidence. Proofline makes the
acceptance boundary executable:

1. Decompose the task into requirements.
2. Collect or receive evidence from authoritative sources.
3. Reject stale, missing, or contradictory evidence.
4. Build a deterministic, hash-addressed proof packet.
5. Pause before any external submission until a human approves it.

## Google stack

- Gemini 3.6 Flash for requirement decomposition and evidence interpretation.
- Google Agent Development Kit (ADK) for the agent and its tools.
- Firestore for durable proof packets and execution state.
- Cloud Run for the hosted agent API.
- Pub/Sub for asynchronous rechecks and long-running verification jobs.

The deterministic verification core runs without cloud credentials, so judges
can inspect and test its safety boundary locally.

## Local verification

```bash
python -m unittest discover -s tests -v
python sample_run.py
```

The ADK agent folder follows Google's discovery convention and contains its own
deployment requirements file. Deployment instructions are in
[`docs/deployment.md`](docs/deployment.md), and the system diagram is in
[`docs/architecture.md`](docs/architecture.md).

## Planned hosted flow

```text
Task -> Gemini/ADK planner -> Pub/Sub verification jobs
     -> authoritative evidence -> deterministic gate
     -> Firestore proof packet -> human approval -> external action
```

No customer data is included in the repository. Demo fixtures are synthetic.

## Current status

- Deterministic evidence gate: implemented and covered by six unit tests.
- Google ADK agent: implemented with a guarded local-development import.
- ADK serving application: exported through the current `App` wrapper with a
  retry-configured Gemini model and an `agents-cli` Cloud Run manifest.
- Firestore, Pub/Sub, and Cloud Run: documented deployment architecture; cloud
  resources are intentionally not provisioned in this repository.
- Devpost project: public at <https://devpost.com/software/proofline-65a8t4>;
  the official hackathon submission remains a draft and no prize or revenue is
  claimed.
- Demo preparation: the 3:45-4:00 recording plan is in
  [`docs/demo-video.md`](docs/demo-video.md). Its cloud segment must be replaced
  with real deployment evidence before publication.
