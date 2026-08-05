# Proofline demo video plan

Target length: 3:45-4:00. Record only the public repository, a local terminal,
the architecture diagram, and the deployed Google Cloud service once it exists.
Do not show credentials, browser profiles, customer data, or private dashboards.

## 0:00-0:25 — The problem

**Screen:** Devpost thumbnail, then the first paragraph of the README.

**Narration:**

> An agent saying “done” is not evidence that the work is complete. Marketplace
> listings go stale, deployments fail silently, and a plausible answer can hide
> missing or contradictory facts. Proofline turns the acceptance boundary into
> something executable and inspectable.

## 0:25-1:05 — Architecture and Google stack

**Screen:** `docs/architecture.md`, slowly following the diagram from left to
right.

**Narration:**

> Gemini 3.6 Flash and Google ADK decompose the task and explain the result.
> Verification jobs can run asynchronously through Pub/Sub. The deterministic
> gate evaluates fresh authoritative evidence, and Firestore stores the
> canonical proof packet. Cloud Run exposes the agent. The language model can
> help reason about evidence, but it cannot override the deterministic gate or
> the human approval boundary.

## 1:05-2:15 — Reproducible local proof

**Screen:** Run these commands in a clean terminal:

```bash
python -m unittest discover -s tests -v
python demo_matrix.py
```

Pause on the passing tests, then scroll through the four deterministic outcomes:
`NEEDS_EVIDENCE`, `CONFLICT`, `APPROVAL_REQUIRED`, and `READY`. Show the
important fields: `unmet`, `conflicts`, `external_action_requested`,
`human_approved`, and `packet_hash`.

**Narration:**

> The verification core is intentionally small and testable. These synthetic,
> fixed-time scenarios show every possible decision. Missing evidence cannot
> pass. Conflicting authorities stop the workflow. Valid evidence with an
> unapproved external action returns APPROVAL_REQUIRED. Only the final approved
> packet is READY. Each SHA-256 hash addresses the exact canonical packet.

## 2:15-3:05 — ADK agent and safety boundary

**Screen:** Show `proofline/agent.py`, then `proofline/tools.py` and the relevant
portion of `proofline/core.py`.

**Narration:**

> The production entry point follows Google ADK's application layout. The agent
> exposes narrowly scoped tools for evaluating evidence and producing a proof
> packet. Model output never directly marks work complete. Only the deterministic
> core can return READY, and any requested external action remains blocked until
> the packet includes explicit human approval.

## 3:05-3:35 — Google Cloud deployment evidence

**Screen:** Show the public Cloud Run URL and the secret-free verification
record in the repository: revision, HTTP 200 discovery/session results, the
Gemini tool call, decision, evidence count, and packet hash. Do not claim
Firestore persistence or Pub/Sub execution; they remain extension points.

**Narration template:**

> This is the live Proofline service on Google Cloud Run. An external request
> discovered the ADK application, created a real session, invoked Gemini 3.6
> Flash, and called the deterministic evidence tool. The resulting READY packet
> hash and the exact deployment evidence are recorded in the public repository.

## 3:35-3:55 — Close

**Screen:** Return to the architecture diagram and thumbnail.

**Narration:**

> Proofline does not make agents sound more certain. It makes their completion
> claims verifiable, tamper-evident, and safe to act on. Proof before finish.

## Publication checklist

- Show only the real Google Cloud evidence recorded in the repository.
- Keep the final video under four minutes.
- Add visible captions and an AI-assisted-production disclosure.
- Verify that no credentials, tokens, email addresses, or private tabs appear.
- Upload to the existing brand channel and attach the public URL to Devpost.
