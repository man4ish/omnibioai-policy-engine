from fastapi import FastAPI
from app.api.routes_policy import router

app = FastAPI(title="OmniBioAI Policy Engine")

app.include_router(router, prefix="/policy")