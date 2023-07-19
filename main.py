from fastapi import FastAPI

app = FastAPI()

from api import info
from api import clova

app.mount("/api/v1/info", info.app)
app.mount("/api/v1/clova", clova.app)
app.mount("/api/v1/speech", speech.app)
