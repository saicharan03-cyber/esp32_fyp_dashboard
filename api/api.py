from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
latest_data = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/update")
async def update_data(request: Request):
    global latest_data
    latest_data = await request.json()
    return {"message": "Data received"}

@app.get("/latest")
def get_latest_data():
    return latest_data
