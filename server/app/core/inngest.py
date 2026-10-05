import logging

from inngest import Inngest

from app.core.config import config

inngest_clent = Inngest(
    app_id="pyrags-app",
    is_production=config.APP_ENV == "production",
    event_key=config.INNGEST_EVENT_KEY,
    signing_key=config.INNGEST_SIGNING_KEY,
    logger=logging.getLogger("uvicorn"),
)
