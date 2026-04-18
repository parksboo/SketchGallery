# Unified Webserver (Flask + UI/API)

This webserver is a single Flask app that serves:
- UI routes: `/`, `/create`, `/gallery`, `/jobs/<id>`
- API routes: `/api/v1/jobs`, `/api/v1/jobs/<id>`, `/api/v1/gallery`
  - `POST /api/v1/jobs` expects JSON metadata (`sketch_key`, `title`, `prompt`, `style`)
  - `GET /api/v1/uploads/config` returns dataplane upload endpoint

It uses PostgreSQL for metadata and delegates file transfer to the dataplane service.

## Local run
```bash
cd SketchGallery
pip install -r requirements.txt
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=sketchgallery
export PGUSER=sketchgallery
export PGPASSWORD=sketchgallery
export DATAPLANE_INTERNAL_URL=http://127.0.0.1:8080
export DATAPLANE_PUBLIC_URL=http://127.0.0.1:8080
python3 src/webserver/app.py
```

## Build image
```bash
cd SketchGallery
docker build -f src/webserver/Dockerfile -t sketchgallery-web:latest .
```

## Deploy to Kubernetes
```bash
kubectl apply -f src/webserver/webserver-k8s.yaml
kubectl get deploy,svc,pods -l app=sketchgallery-web
```

Note: deploy dataplane first (`src/dataplane/dataplane-k8s.yaml`).
`DATAPLANE_PUBLIC_URL` must be reachable by end-user browsers (typically an ingress URL).
