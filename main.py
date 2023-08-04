from fastapi import FastAPI

app = FastAPI()

from api.controller.info import app as info_app
from api.controller.speech import app as speech_app

app.mount("/api/v1/info", info_app)
app.mount("/api/v1/presentations", speech_app)
