FROM python:3.8.17

WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install -r ./requirements.txt

COPY . /app

RUN ["apt-get", "-y", "update"]
RUN ["apt-get", "-y", "upgrade"]
RUN ["apt-get", "install", "-y", "--no-install-recommends", "ffmpeg"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
