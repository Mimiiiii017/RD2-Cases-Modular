from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.cases import router
import os
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(title="Caseflow API — Architecture B (Modular)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)