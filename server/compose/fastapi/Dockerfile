FROM python:3.10-slim-bullseye
# https://github.com/docker/for-mac/issues/5548 must be >=bullseye for mac 

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir backend
RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Additional dependencies
  && apt-get install -y telnet netcat \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./backend/requirements.txt /backend/requirements.txt
RUN pip install -r /backend/requirements.txt

COPY ./compose/fastapi/entrypoint /backend/entrypoint
RUN sed -i 's/\r$//g' /backend/entrypoint
RUN chmod +x /backend/entrypoint

COPY ./compose/fastapi/start /backend/start
RUN sed -i 's/\r$//g' /backend/start
RUN chmod +x /backend/start

COPY ./compose/fastapi/celery/worker/start /backend/start-celeryworker
RUN sed -i 's/\r$//g' /backend/start-celeryworker
RUN chmod +x /backend/start-celeryworker

COPY ./compose/fastapi/celery/beat/start /backend/start-celerybeat
RUN sed -i 's/\r$//g' /backend/start-celerybeat
RUN chmod +x /backend/start-celerybeat

COPY ./compose/fastapi/celery/flower/start /backend/start-flower
RUN sed -i 's/\r$//g' /backend/start-flower
RUN chmod +x /backend/start-flower

WORKDIR /backend
RUN mkdir app
ADD ./backend /backend/app

WORKDIR /backend/app

ENTRYPOINT ["/backend/entrypoint"]