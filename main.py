# main.py
from fastapi import FastAPI

app = FastAPI(title="M3 Lab Backend", version="1.0.0")

@app.get("/")
def home():
    return {"message": "M3 Backend is live!", "status": "ok"}

@app.get("/ping")
def ping():
    return {"status": "ok"}