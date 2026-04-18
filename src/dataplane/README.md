# SketchGallery Data Plane

Dedicated service for high-volume file transfer:
- Direct client upload: `POST /api/v1/files`
- File serving: `GET /files/<key>`
- In-service copy: `POST /api/v1/files/copy`

## Local run
```bash
cd SketchGallery
pip install -r requirements.txt
python3 src/dataplane/app.py
```

## Build image
```bash
docker build -f src/dataplane/Dockerfile -t sketchgallery-dataplane:latest .
```

## Deploy to Kubernetes
```bash
kubectl apply -f src/dataplane/dataplane-k8s.yaml
kubectl get deploy,svc,pods -l app=sketchgallery-dataplane
```

Optional single-pod manifest:
```bash
kubectl apply -f src/dataplane/dataplane-pod.yaml
```
