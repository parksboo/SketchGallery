#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"

echo "[webserver] health check"
curl -fsS "${BASE_URL}/health"
echo

echo "[webserver] upload check"
RESP=$(curl -fsS -X POST "${BASE_URL}/api/v1/jobs" \
  -F "prompt=test-from-webserver-script" \
  -F "sketch=@${1:-images/architecture.drawio.png}")
echo "${RESP}"

echo "[webserver] status check"
JOB_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"${RESP}")
curl -fsS "${BASE_URL}/api/v1/jobs/${JOB_ID}"
echo
