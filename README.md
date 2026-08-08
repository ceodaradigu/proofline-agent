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
python demo_matrix.py
```

`demo_matrix.py` renders one deterministic packet for each possible decision:
`NEEDS_EVIDENCE`, `CONFLICT`, `APPROVAL_REQUIRED`, and `READY`. It uses only
synthetic public-safe fixtures and a fixed UTC evaluation time, so judges can
reproduce the same four packet hashes without credentials or network access.

## Arm64 evidence workflow

The candidate Arm Cloud AI work is kept separate from the existing Cloud Run
submission. On an actual `aarch64` or `arm64` host, run:

```bash
./scripts/run_arm_evidence.sh
```

The runner refuses non-Arm hosts, executes the test suite, performs at least
three deterministic benchmark repetitions, and writes the evidence under
`artifacts/arm64/`. No Arm performance improvement is claimed until those
artifacts exist and the measurements support it. The script does not create
cloud resources or change billing.

The ADK agent folder follows Google's discovery convention and contains its own
deployment requirements file. Deployment instructions are in
[`docs/deployment.md`](docs/deployment.md), and the system diagram is in
[`docs/architecture.md`](docs/architecture.md).

The credential-free ADK API preflight, measured endpoint results, and exact
reproduction commands are recorded in
[`docs/local-api-evidence.md`](docs/local-api-evidence.md).

The contest-requirement matrix and public endpoint checks are recorded in
[`docs/submission-evidence.md`](docs/submission-evidence.md).

## Live deployment

Proofline is live on Google Cloud Run in `europe-west1`:

<https://proofline-343140361830.europe-west1.run.app>

The public ADK API is deployed as revision `proofline-00001-rqw` with zero
minimum instances, one maximum instance, 512 MiB memory, one CPU, concurrency
20, and startup CPU boost disabled. On 2026-08-05 an external verification
returned `HTTP 200` and `["proofline"]` from `/list-apps`, created a real ADK
session, invoked Gemini 3.6 Flash, called the deterministic `evaluate_packet`
tool, and returned `READY` with packet hash
`973750f90ceffd925eba6716399f9064fcc789522ae8455efe764ef6c841eb5d`.

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
- Cloud Run container: reproducible root `Dockerfile` starts the ADK API server
  on the platform-provided port and excludes local secrets from the image.
- Cloud Run: publicly deployed and verified end to end with Gemini and the
  deterministic evidence gate. Firestore and Pub/Sub remain documented
  extension points and are not required by the current in-memory demo.
- Devpost project: officially submitted to the All Things Agentic Hackathon at
  <https://devpost.com/software/proofline-65a8t4>. The public 2:53 demo is at
  <https://youtu.be/khPpdq7GcTk>. No prize or revenue is claimed unless an
  organizer confirms an award and payment.
- Demo preparation: the 3:45-4:00 recording plan is in
  [`docs/demo-video.md`](docs/demo-video.md). The live Cloud Run evidence above
  is the authoritative source for its hosted segment.
