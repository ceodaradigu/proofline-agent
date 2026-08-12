#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

architecture="$(uname -m)"
case "$architecture" in
  aarch64|arm64) ;;
  *)
    echo "Refusing to create Arm evidence on architecture: $architecture" >&2
    exit 2
    ;;
esac

iterations="${PROOFLINE_BENCHMARK_ITERATIONS:-10000}"
repeats="${PROOFLINE_BENCHMARK_REPEATS:-3}"
artifact_dir="${PROOFLINE_ARTIFACT_DIR:-artifacts/arm64}"

python_bin="${PROOFLINE_PYTHON:-}"
if [[ -z "$python_bin" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  else
    echo "Python 3 is required to run the Arm evidence workflow" >&2
    exit 2
  fi
fi

if ! [[ "$iterations" =~ ^[1-9][0-9]*$ ]]; then
  echo "PROOFLINE_BENCHMARK_ITERATIONS must be a positive integer" >&2
  exit 2
fi
if ! [[ "$repeats" =~ ^[1-9][0-9]*$ ]]; then
  echo "PROOFLINE_BENCHMARK_REPEATS must be a positive integer" >&2
  exit 2
fi

mkdir -p "$artifact_dir"

"$python_bin" -m unittest discover -s tests -v 2>&1 | tee "$artifact_dir/tests.txt"
"$python_bin" -m benchmarks.arm_core_benchmark \
  --iterations "$iterations" \
  --repeats "$repeats" \
  --output "$artifact_dir/benchmark.json"
"$python_bin" -m benchmarks.arm_optimization_benchmark \
  --output "$artifact_dir/optimization.json"

"$python_bin" - "$artifact_dir/benchmark.json" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
result = json.loads(path.read_text(encoding="utf-8"))
architecture = str(result.get("architecture", "")).casefold()
if architecture not in {"aarch64", "arm64"}:
    raise SystemExit(f"benchmark did not record Arm64: {architecture!r}")
if result.get("decision") != "READY":
    raise SystemExit("benchmark fixture did not remain READY")
if int(result.get("repeats", 0)) < 3:
    raise SystemExit("at least three benchmark repetitions are required")
print(json.dumps(result, indent=2, sort_keys=True))
PY

"$python_bin" - "$artifact_dir/optimization.json" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
result = json.loads(path.read_text(encoding="utf-8"))
architecture = str(result.get("architecture", "")).casefold()
if architecture not in {"aarch64", "arm64"}:
    raise SystemExit(f"optimization benchmark did not record Arm64: {architecture!r}")
if result.get("decision") != "READY":
    raise SystemExit("optimization benchmark fixture did not remain READY")
if int(result.get("repeats", 0)) < 3:
    raise SystemExit("at least three optimization repetitions are required")
if float(result.get("speedup", 0)) <= 0:
    raise SystemExit("optimization benchmark did not produce a valid speedup ratio")
print(json.dumps(result, indent=2, sort_keys=True))
PY
