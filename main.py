from fastapi import FastAPI

app = FastAPI()

from api import info

app.mount("/api/v1/info", info.app)
