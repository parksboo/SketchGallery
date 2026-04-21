#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

NAMESPACE="${NAMESPACE:-default}"
GCS_BUCKET="${GCS_BUCKET:-}"
RAY_SHARED_TOKEN="${RAY_SHARED_TOKEN:-}"
RAY_ADDRESS="${RAY_ADDRESS:-}"

RAY_FILE="$ROOT_DIR/src/raycluster/raycluster-k8s.yaml"

usage() {
  cat <<USAGE
Usage: $(basename "$0") <command>

Commands:
  up           Deploy ray service/deployment
  down         Remove ray service/deployment
  status       Show ray deploy/svc/pods status
  logs         Tail ray logs

Environment variables:
  ENV_FILE         Path to env file (default: <repo>/.env)
  NAMESPACE        Kubernetes namespace (default: default)
  GCS_BUCKET       GCS bucket name (required)
  RAY_SHARED_TOKEN Shared token for web<->ray auth (required)
  RAY_ADDRESS      Ray cluster address, e.g. ray://ray-head.ray.svc.cluster.local:10001 (required)

Examples:
  ./scripts/ray-stack.sh up
  ./scripts/ray-stack.sh status
USAGE
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Required command not found: $1" >&2
    exit 1
  }
}

require_vars() {
  if [[ -z "$GCS_BUCKET" ]]; then
    echo "[ERROR] GCS_BUCKET is required" >&2
    exit 1
  fi
  if [[ -z "$RAY_SHARED_TOKEN" ]]; then
    echo "[ERROR] RAY_SHARED_TOKEN is required" >&2
    exit 1
  fi
  if [[ -z "$RAY_ADDRESS" ]]; then
    echo "[ERROR] RAY_ADDRESS is required" >&2
    exit 1
  fi
}

apply_ray() {
  require_vars

  local tmp
  tmp="$(mktemp)"
  sed \
    -e "s|REPLACE_WITH_GCS_BUCKET|${GCS_BUCKET}|g" \
    -e "s|REPLACE_WITH_RAY_SHARED_TOKEN|${RAY_SHARED_TOKEN}|g" \
    -e "s|REPLACE_WITH_RAY_ADDRESS|${RAY_ADDRESS}|g" \
    "$RAY_FILE" > "$tmp"
  kubectl -n "$NAMESPACE" apply -f "$tmp"
  rm -f "$tmp"
}

remove_ray() {
  kubectl -n "$NAMESPACE" delete -f "$RAY_FILE" --ignore-not-found
}

status_ray() {
  kubectl -n "$NAMESPACE" get deploy,svc,pods -l app=sketchgallery-ray
}

logs_ray() {
  kubectl -n "$NAMESPACE" logs deployment/sketchgallery-ray -f --tail=200
}

main() {
  require_cmd kubectl
  require_cmd sed

  local cmd="${1:-}"
  case "$cmd" in
    up)
      apply_ray
      status_ray
      ;;
    down)
      remove_ray
      ;;
    status)
      status_ray
      ;;
    logs)
      logs_ray
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
