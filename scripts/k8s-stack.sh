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
RAY_GENERATION_URL="${RAY_GENERATION_URL:-}"
RAY_SHARED_TOKEN="${RAY_SHARED_TOKEN:-}"
WEB_PUBLIC_BASE_URL="${WEB_PUBLIC_BASE_URL:-}"

POSTGRES_SECRET_FILE="$ROOT_DIR/src/postgres/postgres-secret.example.yaml"
POSTGRES_FILE="$ROOT_DIR/src/postgres/postgres-k8s.yaml"
WEBSERVER_FILE="$ROOT_DIR/src/webserver/webserver-k8s.yaml"

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  up            Deploy postgres + webserver
  down          Remove webserver + postgres
  status        Show current deploy/svc/pod status
  logs-web      Tail webserver logs

Environment variables:
  ENV_FILE      Path to env file (default: <repo>/.env)
  NAMESPACE     Kubernetes namespace (default: default)
  GCS_BUCKET    GCS bucket name for signed URL issue (required for up)
  RAY_GENERATION_URL  External Ray generation API endpoint (required for up)
  RAY_SHARED_TOKEN    Shared bearer token for webserver<->ray auth (optional)
  WEB_PUBLIC_BASE_URL Public web URL for Ray callback, e.g. https://app.example.com (optional)

Examples:
  GCS_BUCKET=my-sketch-bucket RAY_GENERATION_URL=https://ray.example.com/generate ./scripts/k8s-stack.sh up
  ./scripts/k8s-stack.sh status
  ./scripts/k8s-stack.sh down
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Required command not found: $1" >&2
    exit 1
  }
}

apply_web_with_bucket() {
  if [[ -z "$GCS_BUCKET" ]]; then
    echo "[ERROR] GCS_BUCKET is required for up" >&2
    exit 1
  fi
  if [[ -z "$RAY_GENERATION_URL" ]]; then
    echo "[ERROR] RAY_GENERATION_URL is required for up (external Ray cluster endpoint)" >&2
    exit 1
  fi

  local tmp
  tmp="$(mktemp)"
  sed \
    -e "s|REPLACE_WITH_GCS_BUCKET|${GCS_BUCKET}|g" \
    -e "s|REPLACE_WITH_RAY_GENERATION_URL|${RAY_GENERATION_URL}|g" \
    -e "s|REPLACE_WITH_RAY_SHARED_TOKEN|${RAY_SHARED_TOKEN}|g" \
    -e "s|REPLACE_WITH_WEB_PUBLIC_BASE_URL|${WEB_PUBLIC_BASE_URL}|g" \
    "$WEBSERVER_FILE" > "$tmp"
  kubectl -n "$NAMESPACE" apply -f "$tmp"
  rm -f "$tmp"
}

deploy_all() {
  require_cmd kubectl
  require_cmd sed

  echo "[INFO] Namespace: $NAMESPACE"
  echo "[INFO] GCS_BUCKET: $GCS_BUCKET"
  echo "[INFO] RAY_GENERATION_URL: $RAY_GENERATION_URL"
  if [[ -n "$WEB_PUBLIC_BASE_URL" ]]; then
    echo "[INFO] WEB_PUBLIC_BASE_URL: $WEB_PUBLIC_BASE_URL"
  else
    echo "[WARN] WEB_PUBLIC_BASE_URL is empty; Ray callback URL will not be included in dispatch payload."
  fi

  if ! kubectl -n "$NAMESPACE" get secret postgres-secret >/dev/null 2>&1; then
    echo "[INFO] postgres-secret not found. Applying example secret: $POSTGRES_SECRET_FILE"
    echo "[WARN] Replace POSTGRES_PASSWORD from 'change-me' for non-local usage."
    kubectl -n "$NAMESPACE" apply -f "$POSTGRES_SECRET_FILE"
  else
    echo "[INFO] postgres-secret already exists."
  fi

  echo "[INFO] Applying Postgres resources..."
  kubectl -n "$NAMESPACE" apply -f "$POSTGRES_FILE"

  echo "[INFO] Applying Webserver resources..."
  apply_web_with_bucket

  echo "[INFO] Done. Current status:"
  show_status
}

remove_all() {
  require_cmd kubectl

  echo "[INFO] Removing Webserver resources..."
  kubectl -n "$NAMESPACE" delete -f "$WEBSERVER_FILE" --ignore-not-found

  echo "[INFO] Removing Postgres resources..."
  kubectl -n "$NAMESPACE" delete -f "$POSTGRES_FILE" --ignore-not-found

  echo "[INFO] Remaining related resources:"
  show_status || true
}

show_status() {
  kubectl -n "$NAMESPACE" get deploy,svc,pods \
    -l 'app in (postgres,sketchgallery-web)'
}

logs_web() {
  kubectl -n "$NAMESPACE" logs deploy/sketchgallery-web -f --tail=200
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    up)
      deploy_all
      ;;
    down)
      remove_all
      ;;
    status)
      show_status
      ;;
    logs-web)
      logs_web
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
