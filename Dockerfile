FROM python:3.8.17 AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN pip3 install poetry && poetry install --no-dev

COPY . /app

FROM linuxserver/ffmpeg

COPY --from=builder /app /app

WORKDIR /app

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
