from fastapi import FastAPI

app = FastAPI()

from api import info
from api import speech

app.mount("/api/v1/info", info.app)
app.mount("/api/v1/speech", speech.app)
