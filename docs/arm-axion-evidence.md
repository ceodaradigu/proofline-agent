# Google Axion benchmark evidence

Proofline's deterministic evaluation core was executed on a real Google Cloud
`c4a-standard-1` VM in `us-central1-b` on 2026-08-08. The guest reported
`aarch64`, Linux, CPython 3.13.5, one Arm vCPU, and 4 GB of memory.

## Verified result

- Decision: `READY`
- Iterations per repetition: 10,000
- Repetitions: 3
- Median core throughput: 23,665.171 packets/second
- Core sample throughput: 23,665.171; 23,772.037; 22,843.107 packets/second
- Deterministic packet hash:
  `9162f41d09cac59ac5c5b52cbc732f15b3ab822b6030f741c804870f72ea6576`
- Repository tests on the same host: 15 passed, 0 failed
- Evidence archive SHA-256:
  `80d59d302564216b4280bd2a3c8728500bc6af082d4cba7d5e438cce8cf6ff84`

## Optimization result

The optimized evaluator indexes authoritative evidence once by requirement,
replacing the original repeated requirements-by-evidence scan. On the same
Axion host, with 256 requirements and 1,024 evidence records across five
alternating-order repetitions:

- Original median: 62.539 proof packets/second
- Optimized median: 98.414 proof packets/second
- Measured speedup: **1.5736×** (**57.36% higher throughput**)
- Decision and deterministic packet hash: identical before and after

The machine was deleted with its boot disk after the evidence was copied and
the archive hash was independently rechecked. The comparison artifact contains
every raw timing sample; no cross-machine or x86 result is used for this claim.

## Reproduce

On an Arm64 Linux host with the project dependencies installed:

```bash
PROOFLINE_PYTHON=/path/to/python ./scripts/run_arm_evidence.sh
```

The machine-readable result, test transcript, archive, and checksum are stored
under [`artifacts/`](../artifacts/).
