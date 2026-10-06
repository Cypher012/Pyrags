from uuid import UUID

import inngest

from app.core.inngest import inngest_clent
from app.embeddings.jobs import (
    embed_and_store_batch,
    finish_job,
    mark_failed,
    prepare_chunks,
)


def parse_job_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("job_id must be a string")
    return str(UUID(value))


async def ingestion_failed(ctx: inngest.Context) -> None:
    original_event = ctx.event.data.get("event")
    if not isinstance(original_event, dict):
        return
    data = original_event.get("data")
    if not isinstance(data, dict):
        return
    try:
        job_id = parse_job_id(data.get("job_id"))
    except (TypeError, ValueError):
        return
    await ctx.step.run("mark-failed", mark_failed, job_id)


@inngest_clent.create_function(
    fn_id="process-document",
    trigger=inngest.TriggerEvent(event="pyrags/document.uploaded"),
    retries=4,
    on_failure=ingestion_failed,
    concurrency=[inngest.Concurrency(limit=1, key="event.data.job_id")],
)
async def process_document(ctx: inngest.Context) -> dict[str, str]:
    job_id = parse_job_id(ctx.event.data.get("job_id"))
    manifest = await ctx.step.run("prepare-chunks", prepare_chunks, job_id)
    for batch_index in range(manifest["batch_count"]):
        await ctx.step.run(
            f"embed-store-{batch_index}",
            embed_and_store_batch,
            job_id,
            batch_index,
        )
    return await ctx.step.run("finish-document", finish_job, job_id)
