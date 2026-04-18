#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-default}"
DATAPLANE_PUBLIC_URL="${DATAPLANE_PUBLIC_URL:-http://127.0.0.1:8080}"

POSTGRES_SECRET_FILE="$ROOT_DIR/src/postgres/postgres-secret.example.yaml"
POSTGRES_FILE="$ROOT_DIR/src/postgres/postgres-k8s.yaml"
DATAPLANE_FILE="$ROOT_DIR/src/dataplane/dataplane-k8s.yaml"
WEBSERVER_FILE="$ROOT_DIR/src/webserver/webserver-k8s.yaml"

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  up            Deploy postgres + dataplane + webserver
  down          Remove webserver + dataplane + postgres
  status        Show current deploy/svc/pod status
  logs-web      Tail webserver logs
  logs-data     Tail dataplane logs

Environment variables:
  NAMESPACE             Kubernetes namespace (default: default)
  DATAPLANE_PUBLIC_URL Browser-reachable dataplane URL (default: http://127.0.0.1:8080)

Examples:
  DATAPLANE_PUBLIC_URL=http://127.0.0.1:8080 ./scripts/k8s-stack.sh up
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

apply_web_with_dataplane_url() {
  local tmp
  tmp="$(mktemp)"
  sed "s|http://REPLACE_WITH_BROWSER_REACHABLE_DATAPLANE|${DATAPLANE_PUBLIC_URL}|g" "$WEBSERVER_FILE" > "$tmp"
  kubectl -n "$NAMESPACE" apply -f "$tmp"
  rm -f "$tmp"
}

deploy_all() {
  require_cmd kubectl
  require_cmd sed

  echo "[INFO] Namespace: $NAMESPACE"
  echo "[INFO] DATAPLANE_PUBLIC_URL: $DATAPLANE_PUBLIC_URL"

  if ! kubectl -n "$NAMESPACE" get secret postgres-secret >/dev/null 2>&1; then
    echo "[INFO] postgres-secret not found. Applying example secret: $POSTGRES_SECRET_FILE"
    echo "[WARN] Replace POSTGRES_PASSWORD from 'change-me' for non-local usage."
    kubectl -n "$NAMESPACE" apply -f "$POSTGRES_SECRET_FILE"
  else
    echo "[INFO] postgres-secret already exists."
  fi

  echo "[INFO] Applying Postgres resources..."
  kubectl -n "$NAMESPACE" apply -f "$POSTGRES_FILE"

  echo "[INFO] Applying Dataplane resources..."
  kubectl -n "$NAMESPACE" apply -f "$DATAPLANE_FILE"

  echo "[INFO] Applying Webserver resources..."
  apply_web_with_dataplane_url

  echo "[INFO] Done. Current status:"
  show_status
}

remove_all() {
  require_cmd kubectl

  echo "[INFO] Removing Webserver resources..."
  kubectl -n "$NAMESPACE" delete -f "$WEBSERVER_FILE" --ignore-not-found

  echo "[INFO] Removing Dataplane resources..."
  kubectl -n "$NAMESPACE" delete -f "$DATAPLANE_FILE" --ignore-not-found

  echo "[INFO] Removing Postgres resources..."
  kubectl -n "$NAMESPACE" delete -f "$POSTGRES_FILE" --ignore-not-found

  echo "[INFO] Remaining related resources:"
  show_status || true
}

show_status() {
  kubectl -n "$NAMESPACE" get deploy,svc,pods \
    -l 'app in (postgres,sketchgallery-dataplane,sketchgallery-web)'
}

logs_web() {
  kubectl -n "$NAMESPACE" logs deploy/sketchgallery-web -f --tail=200
}

logs_data() {
  kubectl -n "$NAMESPACE" logs deploy/sketchgallery-dataplane -f --tail=200
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
    logs-data)
      logs_data
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
