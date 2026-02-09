from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .agent import ClaimsAgent
from .models import ClaimResponse

app = FastAPI(title="Synapx Autonomous Claims Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ClaimsAgent()

# API Endpoints
@app.post("/api/process")
async def process_claim(payload: dict = Body(...)):
    content = payload.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    result = agent.process_claim(content)
    return result

# Serve Static Files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if not os.path.exists(static_path):
    os.makedirs(static_path)

app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
