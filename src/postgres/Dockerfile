FROM postgres:16-alpine

ENV POSTGRES_DB=sketchgallery \
    POSTGRES_USER=sketchgallery \
    POSTGRES_PASSWORD=sketchgallery

COPY init.sql /docker-entrypoint-initdb.d/01-init.sql

EXPOSE 5432
