from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(
    title = "Chess RL API",
    description = "Chess Game with self-learning AI using Reinforcement Learning",
    version="1.0.0"
)

## CORS  - allows our react front end to talk to this backend
#Without this, the browser blocks all the request from localhost:5173

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chess RL API is Running!","status":"ok"}
@app.get("/health")
async def health_check():
    return {"status":"healthy"}

