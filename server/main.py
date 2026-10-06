import logging

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.inngest import inngest_clent
from app.router import router
from app.workflows.document_ingestion import process_document
from app.workflows.dispatch_ingestion import dispatch_ingestion

app = FastAPI(
    title="Pyrags",
    description="Document-grounded question answering with real-time ingestion",
    debug=config.DEBUG,
)

inngest.fast_api.serve(app, inngest_clent, [process_document, dispatch_ingestion])

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(router)
