FROM postgres:14-bullseye

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y postgresql-14-pgvector

ADD ./compose/db /docker-entrypoint-initdb.d/