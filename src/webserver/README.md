# Unified Webserver (Flask + UI/API)

This webserver is a single Flask app that serves:
- UI routes: `/`, `/create`, `/gallery`, `/jobs/<id>`
- API routes:
  - `POST /api/v1/uploads/sign` (issue GCS signed upload URL)
  - `POST /api/v1/jobs` (expects JSON metadata: `sketch_key`, `title`, `prompt`, `style`)
  - `GET /api/v1/jobs/<id>`
  - `GET /api/v1/jobs/<id>/result`
  - `GET /api/v1/gallery`
  - `POST /api/v1/internal/ray/jobs/<job_id>/result` (Ray callback)

It uses PostgreSQL for metadata, Google Cloud Storage for image objects, and an externally-managed Ray cluster for generation.

## Local run
```bash
cd SketchGallery
pip install -r requirements.txt

export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=sketchgallery
export PGUSER=sketchgallery
export PGPASSWORD=sketchgallery

export GCS_BUCKET=your-bucket
export GCS_UPLOAD_URL_EXPIRE_SEC=600
export GCS_DOWNLOAD_URL_EXPIRE_SEC=600
export RAY_GENERATION_URL=https://ray.example.com/generate
export RAY_SHARED_TOKEN=your-shared-token
export WEB_PUBLIC_BASE_URL=https://web.example.com

python3 src/webserver/app.py
```

## Build image
```bash
cd SketchGallery
docker build -f src/webserver/Dockerfile -t sketchgallery-web:latest .
```

## Deploy to Kubernetes
```bash
GCS_BUCKET=your-bucket \
RAY_GENERATION_URL=https://ray.example.com/generate \
RAY_SHARED_TOKEN=your-shared-token \
WEB_PUBLIC_BASE_URL=https://web.example.com \
./scripts/k8s-stack.sh up
./scripts/k8s-stack.sh status
```

## GCS IAM / CORS notes
- The webserver identity must be able to sign URLs (`iam.serviceAccounts.signBlob` via Service Account Token Creator or equivalent).
- The webserver identity must have permissions needed for signed URL issuance and metadata access.
- Bucket CORS must allow browser `PUT` for direct upload.
