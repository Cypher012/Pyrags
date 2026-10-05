import logging

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.inngest import inngest_client
from app.router import router
from app.workflows.document_ingestion import process_document

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

app = FastAPI(
    title="Pyrags",
    description="Document-grounded question answering with real-time ingestion",
    debug=config.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)
app.include_router(router)
inngest.fast_api.serve(app, inngest_client, [process_document])
