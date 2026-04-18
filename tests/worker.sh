#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
TIMEOUT="${TIMEOUT:-30}"

RESP=$(curl -fsS -X POST "${BASE_URL}/api/v1/jobs" \
  -F "prompt=test-from-worker-script" \
  -F "sketch=@${1:-images/architecture.drawio.png}")
JOB_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"${RESP}")

echo "[worker] waiting for completion: ${JOB_ID}"
for _ in $(seq 1 "${TIMEOUT}"); do
  STATUS=$(curl -fsS "${BASE_URL}/api/v1/jobs/${JOB_ID}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  if [[ "${STATUS}" == "completed" ]]; then
    echo "[worker] completed"
    exit 0
  fi
  if [[ "${STATUS}" == "failed" ]]; then
    echo "[worker] failed"
    exit 1
  fi
  sleep 1
done

echo "[worker] timeout after ${TIMEOUT}s"
exit 1
