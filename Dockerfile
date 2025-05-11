###########
# BUILDER #
###########

FROM python:3.12.2-alpine AS builder

WORKDIR /usr/src/app

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev linux-headers

COPY ./app ./app
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r ./app/requirements.txt


#######
# APP #
#######

FROM python:3.12.2-alpine AS app

WORKDIR /home/app/web

RUN mkdir -p /app/static /app/media

COPY ./setup.py .

COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*
RUN pip install -e .

COPY ./app ./app
COPY ./entrypoint.sh ./entrypoint.sh
COPY ./pytest.ini ./pytest.ini

RUN addgroup -S app \
    && adduser -S app -G app \
    && apk update \
    && apk add libpq
RUN chown -R app:app .
RUN chown -R app:app /app/static /app/media
USER app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/home/app/web/app

RUN chmod +x ./entrypoint.sh
