#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

run_limit="${PROOFLINE_VM_RUN_LIMIT:-20m}"
artifact_dir="${PROOFLINE_ARTIFACT_DIR:-artifacts/arm64}"
archive_path="${PROOFLINE_ARCHIVE_PATH:-artifacts/proofline-arm64-evidence.tgz}"

case "$run_limit" in
  *[!0-9smhd]*)
    echo "PROOFLINE_VM_RUN_LIMIT must use timeout syntax such as 20m" >&2
    exit 2
    ;;
esac

mkdir -p "$artifact_dir" "$(dirname "$archive_path")"

power_off() {
  status=$?
  trap - EXIT
  sync
  if [[ "${PROOFLINE_AUTO_POWEROFF:-0}" == "1" ]]; then
    echo "Benchmark session finished with status $status; powering off the VM."
    sudo -n shutdown -h now || true
  fi
  exit "$status"
}
trap power_off EXIT

timeout --signal=TERM --kill-after=30s "$run_limit" \
  ./scripts/run_arm_evidence.sh

tar -czf "$archive_path" -C "$(dirname "$artifact_dir")" "$(basename "$artifact_dir")"
sha256sum "$archive_path" | tee "${archive_path}.sha256"
echo "Evidence archive: $archive_path"
