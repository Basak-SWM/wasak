from fastapi import FastAPI

app = FastAPI()

from api import info

app.mount("/api/info", info.app)
