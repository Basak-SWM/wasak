from fastapi import FastAPI

app = FastAPI()


@app.get("/hello-world")
def echo():
    return {"message": "Hello, World!"}
