# Arm Create submission draft

This document is the source of truth for the Devpost submission. Every numeric
claim below comes from the committed Axion artifacts; no prize or revenue is
claimed before an organizer confirms and pays it.

## Public fields

**Project name:** Proofline on Arm

**Tagline:** Evidence-first AI agent with a 57.36% faster deterministic gate on Google Axion.

**Track:** Cloud AI

**Built with:** Arm64, Google Axion, Python, Google ADK, Gemini, FastAPI, Google Cloud

**Source code:**
https://github.com/ceodaradigu/proofline-agent

**Testing and benchmark evidence:**
https://github.com/ceodaradigu/proofline-agent/blob/main/docs/arm-axion-evidence.md

**Public product demo:**
https://proofline-343140361830.europe-west1.run.app/apps/proofline/app-info

**Supporting video:** https://youtu.be/khPpdq7GcTk

The supporting video demonstrates the product flow and is 2:53 long. The
committed Axion artifacts, rather than the video, are the evidence for the Arm
performance claim.

## Project overview

Proofline is a verification-first AI agent for work that must be proven, not
merely declared complete. Gemini and Google ADK turn a task into explicit
requirements; a deterministic evidence gate then rejects missing, stale, or
contradictory evidence and produces a hash-addressed proof packet. External
actions remain behind human approval.

The Arm challenge update targets the expensive part of that gate. The original
implementation compared every requirement with every evidence record. We
replaced that repeated requirements-by-evidence scan with a single index of
authoritative evidence by requirement. This changes the matching work from
O(R x E) to O(R + E) while preserving the final decision and packet hash.

What makes the project stand out is that the optimization claim is packaged as
reproducible evidence rather than a headline benchmark. The repository includes
the preserved baseline, optimized implementation, alternating-order comparison
harness, every raw timing sample, same-host test transcript, machine metadata,
an evidence archive, and its SHA-256 checksum.

## Functionality and output

For a task contract and a set of evidence records, Proofline outputs one of four
deterministic states: NEEDS_EVIDENCE, CONFLICT, APPROVAL_REQUIRED, or READY. It
also emits a stable proof-packet hash so reviewers can confirm that the judged
evidence has not changed.

The Cloud AI optimization was measured on a real Google Cloud
`c4a-standard-1` Axion VM reporting `aarch64`, with one Arm vCPU and 4 GB of
memory. The comparison used 256 requirements, 1,024 evidence records, and five
alternating-order repetitions:

- Preserved baseline median: 62.539 proof packets/second
- Optimized median: 98.414 proof packets/second
- Speedup: 1.5736x
- Throughput improvement: 57.36%
- Decision and deterministic packet hash: identical before and after
- Same-host repository tests: 15 passed, 0 failed

The independent core benchmark also reached a median 23,665.171 packets/second
across three repetitions of 10,000 iterations. No x86 measurement or
cross-machine comparison is used for the 57.36% claim.

## Build, run, and validate on Arm64

1. Start an Arm64 Linux environment. The submitted evidence used Google Axion
   `c4a-standard-1` in `us-central1-b`.
2. Clone the public repository:

   ```bash
   git clone https://github.com/ceodaradigu/proofline-agent.git
   cd proofline-agent
   ```

3. Create a virtual environment and install the project:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e .
   ```

4. Run the complete Arm evidence workflow:

   ```bash
   PROOFLINE_PYTHON="$PWD/.venv/bin/python" ./scripts/run_arm_evidence.sh
   ```

5. Inspect `artifacts/arm64/optimization.json` for all raw baseline and
   optimized timing samples. The harness fails if the baseline and optimized
   proof packets differ.
6. Verify the committed evidence archive:

   ```bash
   sha256sum -c artifacts/proofline-arm64-evidence.tgz.sha256
   ```

   Expected SHA-256:
   `80d59d302564216b4280bd2a3c8728500bc6af082d4cba7d5e438cce8cf6ff84`.

## What changed during the challenge

Proofline existed before this Arm submission, but the Arm optimization work was
created during the challenge: the indexed evaluator, preserved baseline,
comparison benchmark, Arm-only evidence runner, guarded one-shot cloud wrapper,
same-host test capture, and committed Axion evidence are all contained in the
challenge branch. The existing public Cloud Run interface is provided as a
product demonstration; the Arm64 scripts and artifacts are the authoritative
validation path for this entry.

## Responsible AI and data disclosure

The project and presentation were developed with AI assistance and reviewed by
a human entrant. Benchmarks use synthetic fixtures and contain no customer or
personal data. Gemini interprets and decomposes requirements, but the final
packet state and hash are computed by deterministic code. No generated image,
voice, or realistic synthetic person is used in this submission.

## Suggested form answers

**Hardest parts:** Finding compatible hardware or cloud instances; Measuring
performance; Improving inference server performance; Debugging runtime or
compatibility issues.

**Why it should win:** It turns an agent reliability bottleneck into a measured,
reusable Arm64 optimization, and gives judges enough raw evidence to reproduce
or challenge every performance claim.
