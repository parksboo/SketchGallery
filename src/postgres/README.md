# Postgres for SketchGallery

## 1) Build Docker image
```bash
cd SketchGallery/src/postgres
docker build -t sketchgallery-postgres:16 .
```

## 2) Apply Secret (edit password first)
```bash
kubectl apply -f postgres-secret.example.yaml
```

## 3) Deploy to Kubernetes
```bash
kubectl apply -f postgres-k8s.yaml
```

## 4) Verify
```bash
kubectl get pods
kubectl get svc postgres
```

## Connection info inside cluster
- Host: `postgres`
- Port: `5432`
- DB/User/Password: from `postgres-secret`
