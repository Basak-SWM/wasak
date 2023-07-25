from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class SingleStringModel(BaseModel):
    input_string: str


@app.get("/server-time")
def server_time():
    return {"now": datetime.now()}


@app.get("/echo-string")
async def echo_string(input_string: str):
    if not input_string:
        raise HTTPException(
            status_code=400, detail="Query parameter 'input_string' is required."
        )
    else:
        return {"result": input_string}


@app.post("/reverse-string")
async def reverse_string(dto: SingleStringModel):
    if not dto.input_string:
        raise HTTPException(status_code=400, detail="dto.input_string is required.")
    else:
        result = dto.input_string[::-1]
        return {"result": result}


@app.post("/double-string")
async def double_string(dto: SingleStringModel):
    if not dto.input_string:
        raise HTTPException(status_code=400, detail="dto.input_string is required.")
    else:
        return {"result": dto.input_string * 2}
