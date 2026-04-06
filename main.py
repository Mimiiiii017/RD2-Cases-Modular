from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.cases import router
import os
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(title="Caseflow API — Architecture B (Modular)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["URL_TO_FRONTEND"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)