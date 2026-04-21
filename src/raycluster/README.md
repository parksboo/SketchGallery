# Ray Cluster Service

This folder contains all runtime code that should execute in the Ray cluster side.

## Included components
- `app.py`: HTTP service endpoint (`POST /generate`, `GET /health`)
- `generation.py`: generation workflow (currently placeholder copy)
- `storage.py`: GCS copy logic used by Ray side
- `callback.py`: callback to webserver job-status endpoint
- `config.py`: Ray service environment config
- `Dockerfile`: container image for Ray-side service
- `raycluster-k8s.yaml`: Kubernetes manifest example for Ray side

## Request contract (webserver -> ray)
- Method: `POST`
- URL: `${RAY_GENERATION_URL}`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <RAY_SHARED_TOKEN>` (when configured)
- Body:
```json
{
  "job_id": "uuid",
  "sketch_key": "sketches/<uuid>.png",
  "result_key": "results/<job_id>.png",
  "title": "optional",
  "prompt": "optional",
  "style": "optional",
  "callback_url": "https://web.example.com/api/v1/internal/ray/jobs/<job_id>/result",
  "callback_token": "<RAY_SHARED_TOKEN>"
}
```

## Callback contract (ray -> webserver)
- Method: `POST`
- URL: `/api/v1/internal/ray/jobs/<job_id>/result`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <RAY_SHARED_TOKEN>` (when configured)

Success:
```json
{
  "status": "completed",
  "result_key": "results/<job_id>.png"
}
```

Failure:
```json
{
  "status": "failed",
  "error": "model timeout"
}
```

## Local run
```bash
cd SketchGallery
pip install -r requirements.txt

export GCS_BUCKET=your-bucket
export RAY_SHARED_TOKEN=your-token
export RAY_ADDRESS=ray://ray-head.ray.svc.cluster.local:10001
export RAY_NAMESPACE=sketchgallery
export RAY_GET_TIMEOUT_SEC=300
python3 src/raycluster/app.py
```

## Build image
```bash
cd SketchGallery
docker build -f src/raycluster/Dockerfile -t sketchgallery-ray:latest .
```


## Execution model
- `generate_image_remote` uses `@ray.remote` to run generation work on Ray workers.
- `run_generation` calls `.remote(...)` and waits with `ray.get(...)`.
