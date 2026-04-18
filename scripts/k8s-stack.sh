#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-default}"
GCS_BUCKET="${GCS_BUCKET:-}"

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
  NAMESPACE     Kubernetes namespace (default: default)
  GCS_BUCKET    GCS bucket name for signed URL issue (required for up)

Examples:
  GCS_BUCKET=my-sketch-bucket ./scripts/k8s-stack.sh up
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

  local tmp
  tmp="$(mktemp)"
  sed "s|REPLACE_WITH_GCS_BUCKET|${GCS_BUCKET}|g" "$WEBSERVER_FILE" > "$tmp"
  kubectl -n "$NAMESPACE" apply -f "$tmp"
  rm -f "$tmp"
}

deploy_all() {
  require_cmd kubectl
  require_cmd sed

  echo "[INFO] Namespace: $NAMESPACE"
  echo "[INFO] GCS_BUCKET: $GCS_BUCKET"

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
