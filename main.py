from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

from api.controller.info import app as info_app
from api.controller.speech import app as speech_app
from api.controller.chatbot import app as chatbot_app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/v1/info", info_app)
app.mount("/api/v1/presentations", speech_app)
app.mount("/api/v1/ai-chat-logs", chatbot_app)
