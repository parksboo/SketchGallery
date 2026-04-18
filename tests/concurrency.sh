#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
COUNT="${COUNT:-10}"
INPUT_FILE="${1:-images/architecture.drawio.png}"

echo "[concurrency] submitting ${COUNT} jobs"
seq 1 "${COUNT}" | xargs -I{} -P "${COUNT}" sh -c '
  curl -fsS -X POST "'"${BASE_URL}"'/api/v1/jobs" \
    -F "prompt=concurrency-job-{}" \
    -F "sketch=@'"${INPUT_FILE}"'" >/dev/null
'

echo "[concurrency] submitted"
