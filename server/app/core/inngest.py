import logging

from inngest import Inngest

from app.core.config import config

inngest_clent = Inngest(
    app_id="pyrags-app",
    is_production=config.APP_ENV == "production",
    event_key=config.INNGEST_EVENT_KEY or None,
    signing_key=config.INNGEST_SIGNING_KEY or None,
    logger=logging.getLogger("uvicorn"),
)
