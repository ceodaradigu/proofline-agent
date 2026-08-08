# Google Axion benchmark evidence

Proofline's deterministic evaluation core was executed on a real Google Cloud
`c4a-standard-1` VM in `us-central1-b` on 2026-08-08. The guest reported
`aarch64`, Linux, CPython 3.13.5, one Arm vCPU, and 4 GB of memory.

## Verified result

- Decision: `READY`
- Iterations per repetition: 10,000
- Repetitions: 3
- Median throughput: 16,608.925 packets/second
- Sample throughput: 15,943.661; 17,457.199; 16,608.925 packets/second
- Deterministic packet hash:
  `9162f41d09cac59ac5c5b52cbc732f15b3ab822b6030f741c804870f72ea6576`
- Repository tests on the same host: 13 passed, 0 failed
- Evidence archive SHA-256:
  `9f13b7003ec01886e4991431b946280641781e36b805819c7707c6fc46ff3667`

The machine was deleted with its boot disk after the evidence was copied and
the archive hash was independently rechecked. No x86 comparison or performance
improvement is claimed by this measurement alone.

## Reproduce

On an Arm64 Linux host with the project dependencies installed:

```bash
PROOFLINE_PYTHON=/path/to/python ./scripts/run_arm_evidence.sh
```

The machine-readable result, test transcript, archive, and checksum are stored
under [`artifacts/`](../artifacts/).
