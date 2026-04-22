source ../myvenv/bin/activate

export PYTHONPATH=/home/duki1071/SketchGallery/src:$PYTHONPATH

export HOST=0.0.0.0
export PORT=8000
export GCS_BUCKET=final_project_1071
export GOOGLE_APPLICATION_CREDENTIALS=/home/duki1071/SketchGallery/key_file.json
export RAY_ADDRESS=
export RAY_NAMESPACE=sketchgallery
export RAY_GET_TIMEOUT_SEC=300
export CALLBACK_TIMEOUT_SEC=30

export HF_PROVIDER=replicate
export HF_MODEL=black-forest-labs/FLUX.2-dev
export HF_TOKEN_ENV=HF_TOKEN
export HF_TOKEN=!!!!!!!!!!!!!!!!!!!!!!!!!!


python3 -u src/raycluster/app.py


