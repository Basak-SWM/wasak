from fastapi import FastAPI

app = FastAPI()


@app.post("/{speech_id}/analysis-1")
def trigger_analysis_1():
    return None


@app.post("/{speech_id}/analysis-2")
def trigger_analysis_2():
    return None
