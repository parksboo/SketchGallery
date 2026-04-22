source ../myvenv/bin/activate

export PYTHONPATH=/home/duki1071/SketchGallery/src:$PYTHONPATH

export HOST=0.0.0.0
export PORT=5050
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=sketchgallery
export PGUSER=sketchgallery
export PGPASSWORD=sketchgallery
export GCS_BUCKET=final_project_1071
export GOOGLE_APPLICATION_CREDENTIALS=/home/duki1071/SketchGallery/key_file.json
export RAY_GENERATION_URL=http://127.0.0.1:8000/generate
export WEB_PUBLIC_BASE_URL=http://127.0.0.1:5050
export DEFAULT_GENERATION_MODE=hf
#export DEFAULT_GENERATION_MODE=test

python3 -u src/webserver/app.py
