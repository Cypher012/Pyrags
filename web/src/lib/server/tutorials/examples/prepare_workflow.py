from uuid import UUID

import inngest

from app.core.inngest import inngest_client
from app.embeddings.jobs import prepare_chunks


def parse_job_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("job_id must be a string")
    return str(UUID(value))


@inngest_client.create_function(
    fn_id="process-document",
    trigger=inngest.TriggerEvent(event="pyrags/document.uploaded"),
    retries=4,
)
async def process_document(ctx: inngest.Context) -> dict[str, int]:
    job_id = parse_job_id(ctx.event.data.get("job_id"))
    return await ctx.step.run("prepare-chunks", prepare_chunks, job_id)
